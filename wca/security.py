# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import ctypes
import errno
import logging
import os
import socket
import ssl
import time
from kazoo.handlers.threading import SequentialThreadingHandler
from kazoo.handlers.utils import _set_default_tcpsock_options
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from dataclasses import dataclass
from typing import Optional, Union
from wca import logger
from wca.config import ValidationError, Path


LIBC = ctypes.CDLL('libc.so.6', use_errno=True)

log = logging.getLogger(__name__)

# See http://man7.org/linux/man-pages/man2/perf_event_open.2.html for details on the file and values
PARANOID_FILE = '/proc/sys/kernel/perf_event_paranoid'
ALLOW_CPU_EVENTS = 0

# The constant and enums needs to be redefined in Python as ctypes does not allow to access them
# as they are precompiler macros.
# Value: https://elixir.bootlin.com/linux/v3.10.108/source/include/uapi/linux/capability.h#L104
CAP_DAC_OVERRIDE = 2
# Value: https://elixir.bootlin.com/linux/v3.10.108/source/include/uapi/linux/capability.h#L142
CAP_SETUID = 128

# Version 3 does not seem to work and version 2 is deprecated.
# See: http://man7.org/linux/man-pages/man2/capget.2.html#DESCRIPTION
LINUX_CAPABILITY_VERSION_1 = 0x19980330

GLOBAL_ROOT_UID = 0

HTTP_RESPONSE_MAX_SIZE = 1024


# We need a class that can be mapped to __user_cap_header_struct.
# See: http://man7.org/linux/man-pages/man2/capget.2.html#DESCRIPTION
class UserCapHeaderStruct(ctypes.Structure):
    _fields_ = [("version", ctypes.c_uint32), ("pid", ctypes.c_int)]


# We need a class that can be mapped to __user_cap_data_struct.
# See: http://man7.org/linux/man-pages/man2/capget.2.html#DESCRIPTION
class UserCapDataStruct(ctypes.Structure):
    _fields_ = [
        ("effective", ctypes.c_uint32),
        ("permitted", ctypes.c_uint32),
        ("inheritable", ctypes.c_uint32)
    ]


class GettingCapabilitiesFailed(Exception):
    pass


def are_privileges_sufficient(rdt_enabled) -> bool:
    uid = os.geteuid()
    paranoid = _read_paranoid()
    capabilities = _get_capabilities()
    log.debug("Process capabilities: effective - {}, permitted - {}, inheritable - {}"
              .format(capabilities.effective, capabilities.permitted, capabilities.inheritable))
    has_cap_dac_override = capabilities.effective & CAP_DAC_OVERRIDE == CAP_DAC_OVERRIDE
    has_cap_setuid = capabilities.effective & CAP_SETUID == CAP_SETUID
    log.debug("Determining privileges necessary to call run WCA - uid: {}, paranoid: {}, "
              "CAP_DAC_OVERRIDE: {}".format(uid, paranoid, has_cap_dac_override))
    return uid == GLOBAL_ROOT_UID or \
        paranoid <= ALLOW_CPU_EVENTS and (rdt_enabled is False or
                                          (has_cap_dac_override and has_cap_setuid))


def _get_capabilities():
    header = UserCapHeaderStruct()
    header.pid = os.getpid()
    header.version = LINUX_CAPABILITY_VERSION_1
    data = UserCapDataStruct()
    err = LIBC.capget(ctypes.byref(header), ctypes.byref(data))
    if err != 0:
        raise GettingCapabilitiesFailed("Unable to get capabilities of {}".format(os.getpid()))
    return data


def _read_paranoid() -> int:
    with open(PARANOID_FILE, 'r') as f:
        return int(f.read())


class SetEffectiveRootUid:
    def __enter__(self):
        self.uid = os.geteuid()
        if self.uid != 0:
            os.seteuid(0)
            log.log(logger.TRACE, "Effective user id from {} to 0".format(self.uid))

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            log.warning("Exception {} with message {} thrown".format(exc_type, exc_val))
        if self.uid != 0:
            os.seteuid(self.uid)
            log.log(logger.TRACE, "Effective user id from 0 to {}".format(self.uid))
            self.uid = 0


@dataclass
class SSL:
    server_verify: Union[bool, Path(absolute=True, mode=os.R_OK)] = True
    client_cert_path: Optional[Path(absolute=True, mode=os.R_OK)] = None
    client_key_path: Optional[Path(absolute=True, mode=os.R_OK)] = None

    def __post_init__(self):
        if self.client_key_path and not self.client_cert_path:
            # There is only client key path, that is wrong, throw error.
            raise ValidationError(
                    'Provided client key without certificate!')

    def get_client_certs(self):
        """Return client cert and key path.
        """
        if self.client_cert_path and self.client_key_path:
            # Both are provided, so return tuple.
            return (self.client_cert_path, self.client_key_path)

        # Otherwise return None or path to .pem file which consists client cert and key.
        return self.client_cert_path


SECURE_CIPHERS = ':'.join([
    #   Commented algorithms are not supported in Centos7
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-RSA-AES128-GCM-SHA256',
    'ECDH-ECDSA-AES128-GCM-SHA256',
    'DHE-RSA-AES128-GCM-SHA256',
    'AES128-GCM-SHA256',
    #   'ECDHE-ECDSA-AES128-CCM',
    'ECDHE-ECDSA-AES128-SHA256',
    'ECDHE-RSA-AES128-SHA256',
    #   'ECDHE-ECDSA-AES256-CCM',
    #   'AES128-CCM',
    'AES128-SHA256',
    #   'AES256-CCM',
    'AES256-SHA256',
    #   'DHE-RSA-AES128-CCM',
    'DHE-RSA-AES128-SHA256',
    #   'DHE-RSA-AES256-CCM',
    'DHE-RSA-AES256-SHA256',
    'DHE-DSS-AES128-GCM-SHA256',
    'DHE-DSS-AES128-SHA256',
    'DHE-DSS-AES256-SHA256',
    #   '@SECLEVEL=2',
    ])

SECURE_OPTIONS = 0
SECURE_OPTIONS |= ssl.OP_NO_SSLv2
SECURE_OPTIONS |= ssl.OP_NO_SSLv3
SECURE_OPTIONS |= ssl.OP_NO_TLSv1
SECURE_OPTIONS |= ssl.OP_NO_COMPRESSION


#   Definition copied from kazoo.handlers.utils and modified.
#   Same code is commited in master but not released yet.
#   After release version 2.6.2 it would be removed.
def create_tcp_connection(module, address, timeout=None,
                          use_ssl=False, ca=None, certfile=None,
                          keyfile=None, keyfile_password=None,
                          verify_certs=True, options=None, ciphers=None):
    end = None
    if timeout is None:
        # thanks to create_connection() developers for
        # this ugliness...
        timeout = module.getdefaulttimeout()
    if timeout is not None:
        end = time.time() + timeout
    sock = None

    while True:
        timeout_at = end if end is None else end - time.time()
        # The condition is not '< 0' here because socket.settimeout treats 0 as
        # a special case to put the socket in non-blocking mode.
        if timeout_at is not None and timeout_at <= 0:
            break

        if use_ssl:
            # Disallow use of SSLv2 and V3 (meaning we require TLSv1.0+)
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)

            if options is not None:
                context.options = options
            else:
                context.options |= ssl.OP_NO_SSLv2
                context.options |= ssl.OP_NO_SSLv3

            if ciphers:
                context.set_ciphers(ciphers)

            # Load default CA certs
            context.load_default_certs(ssl.Purpose.SERVER_AUTH)
            context.verify_mode = (
                ssl.CERT_OPTIONAL if verify_certs else ssl.CERT_NONE
            )
            if ca:
                context.load_verify_locations(ca)
            if certfile and keyfile:
                context.verify_mode = (
                    ssl.CERT_REQUIRED if verify_certs else ssl.CERT_NONE
                )
                context.load_cert_chain(certfile=certfile,
                                        keyfile=keyfile,
                                        password=keyfile_password)
            try:
                # Query the address to get back it's address family
                addrs = socket.getaddrinfo(address[0], address[1], 0,
                                           socket.SOCK_STREAM)
                conn = context.wrap_socket(module.socket(addrs[0][0]))
                conn.settimeout(timeout_at)
                conn.connect(address)
                sock = conn
                break
            except ssl.SSLError:
                raise
        else:
            try:
                # if we got a timeout, lets ensure that we decrement the time
                # otherwise there is no timeout set and we'll call it as such
                sock = module.create_connection(address, timeout_at)
                break
            except Exception as ex:
                errnum = ex.errno if isinstance(ex, OSError) else ex[0]
                if errnum == errno.EINTR:
                    continue
                raise

    if sock is None:
        raise module.error

    _set_default_tcpsock_options(module, sock)
    return sock


class HTTPSAdapter(HTTPAdapter):
    """The HTTPs Adapter for urllib3. Provides better security.
    """
    def init_poolmanager(self, *args, **kwargs):
        ssl_context = create_urllib3_context(options=SECURE_OPTIONS, ciphers=SECURE_CIPHERS)
        kwargs['ssl_context'] = ssl_context
        return super(HTTPSAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        ssl_context = create_urllib3_context(options=SECURE_OPTIONS, ciphers=SECURE_CIPHERS)
        kwargs['ssl_context'] = ssl_context
        return super(HTTPSAdapter, self).proxy_manager_for(*args, **kwargs)


class SecureSequentialThreadingHandler(SequentialThreadingHandler):
    def create_connection(self, *args, **kwargs):
        return create_tcp_connection(socket, options=SECURE_OPTIONS, ciphers=SECURE_CIPHERS,
                                     *args, **kwargs)
