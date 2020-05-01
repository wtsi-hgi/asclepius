import logging

DEFAULT_LOGGER = 'asclepius_main'

def init_logger(logger_name, label):
    """Initialises a logger object.

    @param logger_name String passed to the 'logging.getLogger()' function
    @param label String used to prefix every log entry, ie if 'label' == 'CLI'
        every log entry will be formatted 'CLI: (message)'
    """
    #_log_handler = logging.FileHandler(filename='asclepius.log')
    _log_handler = logging.StreamHandler()
    _log_formatter = logging.Formatter(fmt="[%(asctime)s] {}: %(message)s"
        .format(label))

    _log_handler.setFormatter(_log_formatter)
    LOGGER = logging.getLogger(logger_name)
    LOGGER.addHandler(_log_handler)
    LOGGER.setLevel(logging.DEBUG)

    return LOGGER
