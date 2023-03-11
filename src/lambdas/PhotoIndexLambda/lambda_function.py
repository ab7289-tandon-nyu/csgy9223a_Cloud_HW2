import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def lambda_handler(event: dict, context: dict) -> dict:
    logger.debug("Received s3 event: {}".format(event))
    logger.debug("Received context object: {}".format(context))
