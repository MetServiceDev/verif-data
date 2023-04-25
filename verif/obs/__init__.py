import boto3
from os import environ


# environment variables
AWS_PROFILE = environ.get("AWS_PROFILE", None)

# AWS credentials
if AWS_PROFILE:
    boto3.setup_default_session(profile_name=AWS_PROFILE)

session = boto3.Session()
resource_ddb = session.resource("dynamodb", region_name="us-west-2")

# AWS settings
TABLE_NAME = "prod_observations_archive_{year}"
TABLE_NAME_recent = "prod_observations_recent"