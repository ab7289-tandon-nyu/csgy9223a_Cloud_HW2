import logging
import os
import boto3
from botocore.exceptions import ClientError

# from rekognition_objects import RekognitionLabel

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

## ENVIRONMENT ##################################################
OS_DOMAIN: str = "https://vpc-csgy-9332a-hw2-photos-qndp6xmr6xhsptth25dxsx2lra.us-east-1.es.amazonaws.com"
INDEX: str = "photos"
ENDPOINT: str = "_doc"


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


def process_image(image_event: dict, api_client) -> None:
    """
    Parses out the image key and s3 bucket name from the image PUT
    event to be passed on to rekognition
    """
    s3_object: dict = image_event.get("s3")
    if s3_object is None:
        logger.error("s3 object of PUT event was empty %s", image_event)
        return

    bucket_name: str = s3_object["bucket"]["name"] # name
    object_key: str = s3_object["object"]["key"]

    image_object = boto3.resource("s3").Object(
        bucket_name, object_key
    )
    logger.debug("s3 image object: {}".format(image_object))
    rek_image = RekognitionImage.from_bucket(image_object, api_client)
    logger.debug("Rekognition Image Object: %s", rek_image)
    detect_labels(rek_image)


def detect_labels(image_object: RekognitionImage):
    """
    Takes an s3 image object and passes it to rekognition
    for label testing
    """
    if image_object is None:
        logger.error("Unable to detect labels because image object is empty")

    logger.info("begin label detection")
    labels: list = image_object.detect_labels(5)
    print(f"Labels: {labels}")


def lambda_handler(event: dict, context: dict) -> dict:
    logger.debug("Received s3 event: {}".format(event))
    logger.debug("Received context object: {}".format(context))

    url: str = OS_DOMAIN + "/" + INDEX + "/" + ENDPOINT

    rekognition_client = boto3.client("rekognition")

    images_array: list = event.get("Records")
    for image in images_array:
        process_image(image, rekognition_client)
    # TODO
    # Get Object from S3
    # pass object to Rekognition
    # create OpenSearch document from the Rekognition response
    # POST to OpenSearch cluster
