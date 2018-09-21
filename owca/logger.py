import logging
import sys
import time

import colorlog

TRACE = 9

log = logging.getLogger(__name__)


def init_logging(level: str, package_name: str):
    level = level.upper()
    logging.captureWarnings(True)
    logging.addLevelName(TRACE, 'TRACE')
    log_colors = dict(colorlog.default_log_colors, **dict(TRACE='cyan'))

    # formatter and handler
    formatter = colorlog.ColoredFormatter(
        log_colors=log_colors,
        fmt='%(asctime)s %(log_color)s%(levelname)-8s%(reset)s'
            ' %(cyan)s{%(threadName)s} %(blue)s[%(name)s]%(reset)s %(message)s',
    )

    package_logger = logging.getLogger(package_name)
    package_logger.handlers.clear()

    # do not attache the same handler twice
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Module scoped loggers add formatter handler and disable propagation.
    package_logger.addHandler(handler)
    package_logger.propagate = False  # Because we have own handler.
    package_logger.setLevel(level)

    # Inform about tracing level (because of number of metrics).
    package_logger.log(TRACE, 'Package logger trace messages enabled.')

    # Prepare main log to be used by main entry point module
    # (because you cannot create logger before initialization).
    log.debug(
        'setting level=%s for %r package', logging.getLevelName(log.getEffectiveLevel()),
        package_name
    )


def trace(log):
    """Decorator to trace calling of given function reporting all arguments, returned value
    and time of executions.

    Example usage:

    # owca/some_module.py
    log = logging.getLogger(__name__)

    @trace(log)
    def some_function(x):
        return x+1

    some_function(1)

    output in logs (when trace is enabled!)
    [TRACE] owca.some_module: -> some_function(args=(1,), kw={})
    [TRACE] owca.some_module: <- some_function(...) = 2 (time=1.5s)

    """
    def _trace(func):
        def __trace(*args, **kw):
            s = time.time()
            log.log(TRACE, '-> %s(args=%r, kw=%r)', func.__name__, args, kw)
            rv = func(*args, **kw)
            log.log(TRACE, '<- %s(...) = %r (time=%.2fs)', func.__name__, rv, time.time() - s)
            return rv
        return __trace
    return _trace
