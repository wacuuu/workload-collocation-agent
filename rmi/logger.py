import logging
import sys
import time

import colorlog

TRACE = 9

log = logging.getLogger(__name__)


def init_logging(level: str, modules=['rmi']):
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

    for module in modules:

        somelogger = logging.getLogger(module)

        if not somelogger.handlers:
            # do not attache the same handler twice

            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)

            # s3 scoped log add formatter handler and disable propagete
            somelogger.addHandler(handler)
            somelogger.propagate = False

        # main log
        main = logging.getLogger('%s.main' % module)

        if level is not None:
            logging.getLogger(module).setLevel(level)

        somelogger.log(TRACE, 'trace enabled!')
        main.debug('level=%s', logging.getLevelName(main.getEffectiveLevel()))

    if level == 'TRACE':
        rl = logging.getLogger()
        rl.setLevel(TRACE)
        rl.handlers.clear()
        rl.addHandler(handler)
        rl.log(TRACE, 'root trace message enabled!')

        try:
            print('------------------------------------ Logging tree ---------------------')
            import logging_tree
            logging_tree.printout()
            print('------------------------------------ Logging tree END------------------')
        except ImportError:
            log.warning('cannot dump logger hierarchy! pip install logging_tree')
            pass

    return main


def trace(log):
    def _trace(func):
        def __trace(*args, **kw):
            s = time.time()
            log.log(TRACE, '-> %s(args=%r, kw=%r)', func.__name__, args, kw)
            rv = func(*args, **kw)
            log.log(TRACE, '<- %s() = %r (time=%.2fs)', func.__name__, rv, time.time() - s)
            return rv
        return __trace
    return _trace
