# src/signconnect/core/logging.py

import logging
import sys
from typing import Dict, Any

import structlog
from structlog.types import Processor

# Type hint for the event dictionary used by structlog
EventDict = Dict[str, Any]


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configures logging for the application using structlog.

    This setup ensures that all logs are processed as structured JSON,
    which is ideal for production environments and log management systems.

    Pre-conditions:
    - `log_level` must be a valid Python logging level string (e.g., "DEBUG", "INFO").

    Post-conditions:
    - Python's standard logging is integrated with structlog.
    - Log output is directed to stdout in JSON format.
    """
    # A list of processors that will be applied to each log record.
    # Processors are functions that modify the log record dictionary.
    shared_processors: list[Processor] = [
        # Adds contextual data that is bound to the logger.
        structlog.contextvars.merge_contextvars,
        # Adds static information to the log record.
        structlog.stdlib.add_logger_name,
        # Adds the log level (e.g., 'info', 'error') to the record.
        structlog.stdlib.add_log_level,
        # Allows for using %-style formatting in log messages.
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Adds a timestamp to the record.
        structlog.processors.TimeStamper(fmt="iso"),
        # Collects extra keyword arguments from the log call.
        structlog.processors.dict_tracebacks,
        # Standardizes keyword arguments for better consistency.
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure the standard logging library to be a sink for structlog.
    # This allows libraries that use the standard logging to also produce
    # structured logs.
    structlog.configure(
        processors=[
            # This processor is the bridge between structlog and stdlib logging.
            structlog.stdlib.filter_by_level,
            *shared_processors,
            # This must be the last processor in the chain for stdlib.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        # The 'logger_factory' creates the underlying logger instance.
        logger_factory=structlog.stdlib.LoggerFactory(),
        # The 'wrapper_class' is what you get when you call structlog.get_logger().
        wrapper_class=structlog.stdlib.BoundLogger,
        # The 'cache_logger_on_first_use' flag improves performance.
        cache_logger_on_first_use=True,
    )

    # Define the formatter for the standard logging handler.
    # We use JSONRenderer to output logs in JSON format.
    formatter = structlog.stdlib.ProcessorFormatter(
        # The 'foreign_pre_chain' is for logs from other libraries.
        foreign_pre_chain=shared_processors,
        processor=structlog.processors.JSONRenderer(),
    )

    # Set up a handler to write logs to standard output.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Get the root logger and attach our configured handler.
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Special handling for uvicorn loggers to prevent duplicate logs.
    for name in ["uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(name)
        logger.propagate = False
        logger.handlers = [handler]
