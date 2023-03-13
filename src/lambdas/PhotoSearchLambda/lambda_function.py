import os
import requests
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def lambda_handler(event: dict, context: dict) -> None:
    logger.debug("Received search event: {}".format(event))
    logger.debug("Received context object: {}".format(context))
