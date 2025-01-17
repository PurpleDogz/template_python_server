# Custom Logger Using Loguru

import json
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any

import orjson
import structlog
import structlog._log_levels
from asgi_correlation_id.context import correlation_id
from loguru import logger as loguru_logger
from structlog import get_logger

from . import json_formatter

try:
    from . import config
except Exception:
    import config

MODE_STRUCTLOG = 1
MODE_LOGURU = 2

mode = MODE_LOGURU


def getLogger(id):
    if mode == MODE_STRUCTLOG:
        return get_logger(id)
    return logging.getLogger(id)


def add_correlation(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add request id to log message."""
    if request_id := correlation_id.get():
        event_dict["request_id"] = request_id
    return event_dict


def dumps(*a, **kw) -> str:
    try:
        # This raises "dumps() got unexpected keyword argument"
        return orjson.dumps(*a, **kw).decode()

        # This works:
        # return orjson.dumps(*a, default=kw.get("default")).decode()

    except Exception as e:
        return f"ONOES {e} ### {a} ### {kw}"


class CustomRenderLog(object):
    def __call__(self, logger, method_name, event_dict):
        # An example of keying off log message
        # if event_dict.get('event') == "Fizz":
        #     raise structlog.DropEvent
        # # An example of keying off additional data
        # count = event_dict.get('count')
        # if count and count % 3 == 0 and count % 5 != 0:
        #     raise structlog.DropEvent
        event_dict["source"] = config.get().SERVICE_NAME
        event_dict["source_type"] = config.get().SERVICE_MODE
        return event_dict


# _renderer = structlog.processors.JSONRenderer(serializer=dumps, ensure_ascii=False, sort_keys=True)
# def json_renderer(logger, level, event):
#   event['source'] = config.get().SERVICE_NAME
#   event['source_type'] = config.get().SERVICE_MODE
#   return _renderer(logger, level, event)


class InternalEventHandler(logging.Handler):
    def __init__(self, event_logger, min_level=logging.INFO):
        self.event_logger = event_logger
        self.min_level = min_level
        logging.Handler.__init__(self)

    def emit(self, record):
        if record.levelno >= self.min_level:
            self.event_logger.add_message(
                {"topic": "logs", "data": self.format(record)}
            )


def setup_logging(config_path, file_path, file_name, event_logger=None):
    logger_global = None

    if mode == MODE_STRUCTLOG:
        logger_global = logging.getLogger()

        shared_processors = []
        processors = shared_processors + [
            add_correlation,
            # If log level is too low, abort pipeline and throw away log entry.
            structlog.stdlib.filter_by_level,
            # Add the name of the logger to event dict.
            structlog.stdlib.add_logger_name,
            # Add log level to event dict.
            structlog.stdlib.add_log_level,
            # Perform %-style formatting.
            structlog.stdlib.PositionalArgumentsFormatter(),
            # Add a timestamp in ISO 8601 format.
            structlog.processors.TimeStamper(fmt="iso"),
            # If the "stack_info" key in the event dict is true, remove it and
            # render the current stack trace in the "stack" key.
            structlog.processors.StackInfoRenderer(),
            # If the "exc_info" key in the event dict is either true or a
            # sys.exc_info() tuple, remove "exc_info" and render the exception
            # with traceback into the "exception" key.
            structlog.processors.format_exc_info,
            # If some value is in bytes, decode it to a unicode str.
            structlog.processors.UnicodeDecoder(),
            # Add callsite parameters.
            # structlog.processors.CallsiteParameterAdder(
            #     {
            #         structlog.processors.CallsiteParameter.FILENAME,
            #         structlog.processors.CallsiteParameter.FUNC_NAME,
            #         structlog.processors.CallsiteParameter.LINENO,
            #     }
            # ),
            # Render the final event dict as JSON.
            CustomRenderLog(),
            structlog.processors.JSONRenderer(sort_keys=True),
        ]
        structlog.configure(
            cache_logger_on_first_use=True,
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
        )

        config_global = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(serializer=dumps),
                    "foreign_pre_chain": shared_processors,
                },
            },
            "handlers": {
                "stream": {
                    "level": "INFO",
                    "formatter": "json",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["stream"],
                    "level": "DEBUG",
                    "propagate": True,
                },
            },
        }
        logging.config.dictConfig(config_global)

        file_handler = TimedRotatingFileHandler(
            filename=file_path + file_name.lower(),
            interval=1,
            backupCount=48,
            encoding="utf-8",
        )
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer()
            )
        )

        logger_global.addHandler(file_handler)

        if event_logger:
            internal_handler = InternalEventHandler(event_logger)
            internal_handler.setFormatter(json_formatter.JsonFormatter())
            logger_global.addHandler(internal_handler)

    elif mode == MODE_LOGURU:
        internal_handler = None
        if event_logger:
            internal_handler = InternalEventHandler(event_logger)
            internal_handler.setFormatter(json_formatter.JsonFormatter())
        logger_global = CustomizeLogger.make_logger(
            config_path, file_path, file_name, internal_handler
        )

    return logger_global


class InterceptHandler(logging.Handler):
    loglevel_mapping = {
        50: "CRITICAL",
        40: "ERROR",
        30: "WARNING",
        20: "INFO",
        10: "DEBUG",
        0: "NOTSET",
    }

    def emit(self, record):
        try:
            level = loguru_logger.level(record.levelname).name
        except AttributeError:
            level = self.loglevel_mapping[record.levelno]

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        log = loguru_logger.bind(request_id="app")
        log.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class CustomizeLogger:
    @classmethod
    def make_logger(
        cls,
        config_path: Path,
        file_path: Path,
        file_name: str,
        extra_handler: logging.Handler = None,
    ):
        local_config = cls.load_logging_config(config_path)
        logging_config = local_config.get("logger")

        # Override
        logging_config["path"] = file_name
        logging_config["filename"] = file_name

        # Map to data folder
        p = Path(str(file_path) + str(logging_config.get("path")))

        # print("Logging to: " + str(p))

        logger_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> | {thread} | <level>{message}</level>"
        )

        logger = cls.customize_logging(
            p,
            level=logging_config.get("level"),
            retention=logging_config.get("retention"),
            rotation=logging_config.get("rotation"),
            format=logger_format,  # logging_config.get('format')
            extra_handler=extra_handler,
        )
        return logger

    @classmethod
    def customize_logging(
        cls,
        filepath: Path,
        level: str,
        rotation: str,
        retention: str,
        format: str,
        extra_handler: logging.Handler = None,
    ):
        loguru_logger.remove()
        loguru_logger.add(
            sys.stdout, enqueue=True, backtrace=True, level=level.upper(), format=format
        )
        loguru_logger.add(
            str(filepath),
            rotation=rotation,
            retention=retention,
            enqueue=True,
            backtrace=True,
            level=level.upper(),
            format=format,
        )

        handlers = [InterceptHandler()]

        if extra_handler:
            handlers.append(extra_handler)

        logging.basicConfig(handlers=handlers, level=0)

        # logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
        # for _log in ['uvicorn',
        #              'uvicorn.error',
        #              'fastapi'
        #              ]:
        #     _logger = logging.getLogger(_log)
        #     _logger.handlers = [InterceptHandler()]

        return loguru_logger.bind(request_id=None, method=None)

    @classmethod
    def load_logging_config(cls, config_path):
        config = None
        with open(config_path) as config_file:
            config = json.load(config_file)
        return config


# Hacky: fix later..

g_logger = None


def get(event_logger=None) -> logging.Logger:
    global g_logger
    if not g_logger:
        config_path = "logging_config.json"
        g_logger = setup_logging(
            config_path,
            config.get().get_logs_folder(),
            "{}.log".format(config.get().get_log_file_name()),
            event_logger,
        )
    return g_logger
