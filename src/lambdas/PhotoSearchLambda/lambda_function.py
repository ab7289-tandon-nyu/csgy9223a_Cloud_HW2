import os
import requests
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

OS_DOMAIN: str = "https://" + os.getenv("OpenSearch_Domain")


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

    intent: dict = response['sessionState']['intent']
    searchSlot: dict = intent['slots']['SearchTerms']

    return list([slotVal['value']['interpretedValue'] for slotVal in searchSlot['values']])


def lambda_handler(event: dict, context: dict) -> dict:

    print(f"received event: {event}")
    print(f"received context: {context}")

    queryString: str = event["queryStringParameters"]["q"]

    print(f"received queryString: {queryString}")

    searchTerms: list = disambiguate(queryString)

    print(f"disambiguated search terms: {searchTerms}")

    response: dict = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {},
        "multiValueHeaders": {},
        "body": ",".join(searchTerms)
    }

    return response
