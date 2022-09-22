import socket
import logging
import boto3
from botocore.exceptions import ClientError
from constants import *

#resource and client objects
sqs_resource = boto3.resource('sqs')
sqs_client = boto3.client('sqs')