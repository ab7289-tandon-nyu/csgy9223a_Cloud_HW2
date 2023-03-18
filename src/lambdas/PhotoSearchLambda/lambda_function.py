import os
import requests
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event: dict, context: dict) -> None:
    logger.info("Received search event: {}".format(event))
    logger.info("Received context object: {}".format(context))

    print(f"received event: {event}")
    print(f"received context: {context}")

    response: dict = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {},
        "multiValueHeaders": {},
        "body": "test body"
    }

    return response
