import logging


def init_logger(log_level:int = logging.INFO, log_format: str = '%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'):
    logging.basicConfig(format=log_format,
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=log_level)
    log = logging.getLogger(__name__)
    # LogLevel
    return log
