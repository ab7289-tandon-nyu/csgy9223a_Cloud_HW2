import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

## ENVIRONMENT ##################################################
OS_DOMAIN: str = "https://vpc-csgy-9332a-hw2-photos-qndp6xmr6xhsptth25dxsx2lra.us-east-1.es.amazonaws.com"
INDEX: str = "photos"
ENDPOINT: str = "_doc"

def lambda_handler(event: dict, context: dict) -> dict:
    logger.debug("Received s3 event: {}".format(event))
    logger.debug("Received context object: {}".format(context))

    url: str = OS_DOMAIN + "/" + INDEX + "/" + ENDPOINT
