import os
import requests
import boto3
import json
from botocore.exceptions import ClientError
from requests.auth import HTTPBasicAuth
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

OS_DOMAIN: str = "https://" + os.getenv("OpenSearch_Domain")
INDEX: str = "photos"
SEARCH: str = "_search"


def query_opensearch(searchTerms: list[str]) -> list[dict]:
    """
    Queries our opensearch index for images whose labels' array
    contains one of the search terms that user is querying for

    Parameters:
    :searchTerms list: the list of disambiguated search terms
    :returns list: list of s3 object 
    """
    # strip out any trailing 's'
    searchTerms = list(
        map(lambda x: x[:-1] if x.endswith("s") else x, searchTerms))
    # repackage the search terms in the format necessary for the query
    search_query: list = list(
        map(lambda x: {"term": {"labels": x}}, searchTerms))
    query: dict = {
        "query": {
            "bool": {
                "should": search_query
            }
        }
    }

    print(f"built search query: {query}")

    headers: dict = {"Content-Type": "application/json"}
    url: str = OS_DOMAIN + "/" + INDEX + "/" + SEARCH

    auth = HTTPBasicAuth(os.getenv("OpenSearch_User"),
                         os.getenv("OpenSearch_Password"))
    response = requests.get(url, headers=headers, json=query, auth=auth)
    response.raise_for_status()

    return parse_os_response(response.json())


def parse_os_response(response: dict) -> list[dict]:
    """
    Parses the Opensearch response
    """
    hits_obj: dict = response["hits"]
    hit_count: int = hits_obj["total"]["value"]
    if hit_count == 0:
        logger.error("No hits received from opensearch")
        return []
    else:
        logger.info("OpenSearch returned %s hits", hit_count)
        hits_array: list = hits_obj["hits"]
        return build_search_response(hits_array)


def build_search_response(hits: list[dict]) -> list[dict]:
    """
    Taking in an array of hits from OpenSearch, builds the proper
    response for our Search API
    """
    def mapper(hit: dict) -> dict:
        source: dict = hit["_source"]
        return {
            "url": f"https://{source['bucket']}.s3.amazonaws.com/{source['objectKey']}",
            "labels": source["labels"]
        }

    return list(map(mapper, hits))


def disambiguate(query: str) -> list:
    """
    Utilizes our Lex bot to parse out what the user was asking

    Parameters:
    :queryString string: the text string that the user input
    :returns: list of disambiguated search terms.
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
    slots: dict = intent['slots']
    searchSlot: dict = slots.get('SearchTerms')

    if slots is not None:
        return list([slotVal['value']['interpretedValue'] for slotVal in searchSlot['values']])
    else:
        return []


def lambda_handler(event: dict, context: dict) -> dict:

    print(f"received event: {event}")
    print(f"received context: {context}")

    queryString: str = event["queryStringParameters"]["q"]

    print(f"received queryString: {queryString}")

    searchTerms: list = disambiguate(queryString)

    print(f"disambiguated search terms: {searchTerms}")

    s3_img_urls: list[str] = query_opensearch(searchTerms)

    print(f"s3_img_urls: {s3_img_urls}")

    response: dict = {
        "isBase64Encoded": False,
        "statusCode": 200 if len(s3_img_urls) > 0 else 204,
        "headers": {"Content-Type": "application/json",
                    'Access-Control-Allow-Origin': '*', },
        "multiValueHeaders": {},
        "body": json.dumps(s3_img_urls)
    }

    return response
