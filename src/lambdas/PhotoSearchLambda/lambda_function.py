import os
import requests
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def disambiguate(query: str) -> list:
    """
    Utilizes our Lex bot to parse out what the user was asking

    Parameters:
    :queryString string: the text string that the user input
    :returns: list of disambiguated search terms
    """

    client = boto3.client('lexv2-runtime')

    response = client.recognize_text(
        botId=os.getenv("LexBotId"),
        botAliasId=os.getenv("LexBotAliasId"),
        localeId='en_US',
        sessionId='testsession',
        text=query,
    )
    print(f"Lex response: {response}")


def lambda_handler(event: dict, context: dict) -> None:
    logger.info("Received search event: {}".format(event))
    logger.info("Received context object: {}".format(context))

    print(f"received event: {event}")
    print(f"received context: {context}")

    queryString: str = event["queryStringParameters"]["q"]

    print(f"received queryString: {queryString}")

    searchTerms: list = disambiguate(queryString)

    response: dict = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {},
        "multiValueHeaders": {},
        "body": "test body"
    }

    return response
