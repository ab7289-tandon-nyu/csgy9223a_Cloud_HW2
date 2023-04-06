import logging
import os
import boto3
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from botocore.exceptions import ClientError

from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

## ENVIRONMENT ##################################################
OS_DOMAIN: str = "https://" + os.getenv("OpenSearch_Domain")
INDEX: str = "photos"
ENDPOINT: str = "_doc"

OS_URL: str = OS_DOMAIN + "/" + INDEX + "/" + ENDPOINT


class RekognitionImage:
    """
    Encapsulates an Amazon Rekognition image. This class is a thin wrapper
    around parts of the Boto3 Amazon Rekognition API.
    """

    def __init__(self, image, image_name, rekognition_client):
        """
        Initializes the image object.

        :param image: Data that defines the image, either the image bytes or
                      an Amazon S3 bucket and object key.
        :param image_name: The name of the image.
        :param rekognition_client: A Boto3 Rekognition client.
        """
        self.image = image
        self.image_name = image_name
        self.rekognition_client = rekognition_client

    @classmethod
    def from_bucket(cls, s3_object, rekognition_client):
        """
        Creates a RekognitionImage object from an Amazon S3 object.
        :param s3_object: An Amazon S3 object that identifies the image. The image
                          is not retrieved until needed for a later call.
        :param rekognition_client: A Boto3 Rekognition client.
        :return: The RekognitionImage object, initialized with Amazon S3 object data.
        """
        image = {'S3Object': {
            'Bucket': s3_object.bucket_name, 'Name': s3_object.key}}
        return cls(image, s3_object.key, rekognition_client)

    def detect_labels(self, max_labels):
        """
        Detects labels in the image. Labels are objects and people.

        :param max_labels: The maximum number of labels to return.
        :return: The list of labels detected in the image.
        """
        try:
            response = self.rekognition_client.detect_labels(
                Image=self.image, MaxLabels=max_labels)
            # labels = [RekognitionLabel(label) for label in response['Labels']]
            labels = [label for label in response['Labels']]
            logger.info("Found %s labels in %s.", len(labels), self.image_name)
        except ClientError:
            logger.info("Couldn't detect labels in %s.", self.image_name)
            raise
        else:
            return labels


def get_head_object(bucket_name: str, key: str) -> Optional[list]:
    """
    uses the boto3 s3 client to retrieve the head object of an s3 object
    and returns the x-amz-meta-customLabels if it exists

    :param bucket_name: the name of the bucket
    :param key: the key of the object in the bucket
    :returns: an array of custom labels or nothing
    """
    s3 = boto3.client("s3")
    response: dict = s3.head_object(Bucket=bucket_name, Key=key)
    print(f"Received head_object response: {response}")
    metadata: dict = response.get("Metadata")
    return metadata.get("x-amz-meta-customLabels")


def process_image(image_event: dict, api_client) -> None:
    """
    Parses out the image key and s3 bucket name from the image PUT
    event to be passed on to rekognition
    """
    s3_object: dict = image_event.get("s3")
    if s3_object is None:
        logger.error("s3 object of PUT event was empty %s", image_event)
        return

    bucket_name: str = s3_object["bucket"]["name"]  # name
    object_key: str = s3_object["object"]["key"]

    custom_labels: Optional[list] = get_head_object(bucket_name, object_key)

    image_object = boto3.resource("s3").Object(
        bucket_name, object_key
    )
    logger.debug("s3 image object: {}".format(image_object))

    rek_image = RekognitionImage.from_bucket(image_object, api_client)
    logger.debug("Rekognition Image Object: {}".format(rek_image))
    rekog_labels: list = detect_labels(rek_image)

    send_to_os(rekog_labels, custom_labels, object_key, bucket_name)


def send_to_os(rekog_labels: 'list[str]', custom_labels: Optional[list], key: str, bucket: str):
    """
    Indexes the document in OpenSearch
    """
    if custom_labels is not None:
        rekog_labels.extend(custom_labels)

    payload: dict = dict(
        objectKey=key,
        bucket=bucket,
        createdTimestamp=datetime.now().isoformat(),
        labels=rekog_labels
    )

    basic_auth = HTTPBasicAuth(
        os.getenv("OpenSearch_User"), os.getenv("OpenSearch_Passwored"))
    headers: dict = {"Content-Type": "application/json"}

    r = requests.post(OS_URL, json=payload, headers=headers, auth=basic_auth)
    r.raise_for_status()
    logger.debug(
        "{} returned from POST {} - json: {}".format(r.status_code, OS_URL, payload))


def detect_labels(image_object: RekognitionImage) -> list:
    """
    Takes an s3 image object and passes it to rekognition
    for label testing
    """
    if image_object is None:
        logger.error("Unable to detect labels because image object is empty")

    logger.info("begin label detection")
    labels: list = image_object.detect_labels(5)
    logger.info("Rekognition Labels: {}".format(labels))
    return list([label.get("Name") for label in labels])


def lambda_handler(event: dict, context: dict) -> None:
    logger.debug("Received s3 event: {}".format(event))
    logger.debug("Received context object: {}".format(context))

    rekognition_client = boto3.client("rekognition")

    images_array: list = event.get("Records")
    for image in images_array:
        process_image(image, rekognition_client)

    response: dict = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {"Content-Type": "application/json",
                    'Access-Control-Allow-Origin': '*', },
        "multiValueHeaders": {},
        "body": "",
    }
    return response
