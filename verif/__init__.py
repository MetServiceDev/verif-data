from logging import DEBUG, ERROR, INFO, Formatter, StreamHandler, getLogger
from os import environ


# environment variables
LOGGING_LEVEL = environ.get("LOGGING_LEVEL", "info")

# logger function
def get_loggers():
    """config the logger format"""

    if LOGGING_LEVEL == "info":
        log_lev = INFO
    elif LOGGING_LEVEL == "debug":
        log_lev = DEBUG
    elif LOGGING_LEVEL == "error":
        log_lev = ERROR

    formatter = Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch = StreamHandler()
    ch.setLevel(log_lev)
    ch.setFormatter(formatter)

    logger = getLogger()
    logger.setLevel(log_lev)
    logger.addHandler(ch)
    for ignore in (
        "boto",
        "boto3",
        "botocore",
        "requests",
        "urllib3",
        "simple",
        "s3transfer",
    ):
        getLogger(ignore).propagate = False

    return logger
