import logging
import logging.config
import config


def get_logger_by_namespace(name):
    logging.config.dictConfig(config.LOG_CONFIG)
    logger = logging.getLogger(name)
    return logger


def get_logger_by_class(calling_object):
    object_root = calling_object.__module__
    object_class = type(calling_object).__name__
    full_object_path = "{0}:{1}".format(object_root, object_class)
    return get_logger_by_namespace(full_object_path)
