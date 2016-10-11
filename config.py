ENVIRONMENT = 'sandbox'
LOG_CONFIG = None

def set_environment(env):
    global ENVIRONMENT
    ENVIRONMENT = env
    configure_logging(ENVIRONMENT)


def get_env_parameter(property):
    return property.get(ENVIRONMENT, property['sandbox'])


METRICS_ENABLED = True

def configure_logging(env):
    global LOG_CONFIG
    LOG_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(asctime)s - %(levelname)s  %(name)s:%(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            },
        },
        "loggers": {
            "app": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": True
            },
        }
    }


configure_logging(ENVIRONMENT)
