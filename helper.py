import socket
import logging
import boto3
from botocore.exceptions import ClientError
from constants import *

#resource and client objects
sqs_resource = boto3.resource('sqs')
sqs_client = boto3.client('sqs')

s3_client = boto3.client('s3')
s3_res = boto3.resource('s3')

ec2_client = boto3.client('ec2')
ec2_res = boto3.resource('ec2')

def create_queue(queue_name, attributes):
    SQS_QUEUE_NAME = queue_name
    # Create a SQS queue
    response = sqs_client.create_queue(
        QueueName=SQS_QUEUE_NAME, Attributes=attributes)
    return response['QueueUrl']


def get_queue_url(queue_name):
    return sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']


def get_queue_attributes(queue_url):
    # for visible and invisible -> attribute_names = ['All']
    queue_attrs = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=['All'])
    if 'Attributes' in queue_attrs:
        return queue_attrs['Attributes']
    else:
        return {}


def get_one_queue_attribute(queue_url, attribute_name='ApproximateNumberOfMessages'):
    attrs = get_queue_attributes(queue_url)
    if attribute_name in attrs:
        return attrs[attribute_name]
    else:
        return '-'


# send message to queue
def send_message(queue_url, message_attributes, message_group_id, message_body):
    response = sqs_client.send_message(
        QueueUrl=queue_url,
        MessageAttributes=message_attributes,
        MessageGroupId=message_group_id,
        MessageBody=message_body
    )
    return response['MessageId']


# recieve message from queue (wait time as a variable)
def receive_message(queue_url, num_messages):
    return sqs_client.receive_message(
        QueueUrl=queue_url,
        AttributeNames=['All'],
        MessageAttributeNames=['All'],
        MaxNumberOfMessages=num_messages,
    )


def delete_message(queue_url, receipt_handle):
    sqs_client.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )

# S3

# create bucket (if it doesn't exist)


def create_bucket(bucket_name, region=None):
    try:
        if region is None:
            s3_client.create_bucket(Bucket=bucket_name)
            print("bucket created", bucket_name)
        else:
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name,
                                    CreateBucketConfiguration=location)
    except ClientError as e:
        logging.error(e)
    # return success status
        return False
    return True


# add to bucket
def upload_file(file_name, bucket_name, object_name):
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name
    # Upload the file
    try:
        response = s3_client.upload_file(file_name, bucket_name, object_name)
        print(response)
    except ClientError as e:
        logging.error(e)
    # return success status
        return False
    return True

# read from bucket


def read_from_bucket(bucket_name, object_name):
    # check if bucket exists
    bucket = s3_res.Bucket(bucket_name)
    object = bucket.Object(object_name)
    print(object)
    # downloading file to local from bucket
    object.download_file(object_name)


def get_instance_id():
    hostname = '{}.ec2.internal'.format(socket.gethostname())
    filters = [{'Name': 'private-dns-name', 'Values': [hostname]}]
    response = ec2_client.describe_instances(Filters=filters)["Reservations"]
    return response[0]['Instances'][0]['InstanceId']
# EC2
# create instances (ami code)


def create_instance(key_name, sec_group_ids, image_id='ami-0ee8cf7b8a34448a6', instance_type='t2.micro', min_count=1, max_count=1):

    instancelist = ec2_res.create_instances(
        ImageId=image_id,
        MinCount=min_count,
        MaxCount=max_count,
        InstanceType=instance_type,
        KeyName=key_name,
        SecurityGroupIds=[sec_group_ids],
        UserData=USERDATA,
        IamInstanceProfile=INSTANCE_PROFILE
    )

    for i in range(max_count):
        j = i+1
        instance_id = instancelist[i].instance_id
        print(instance_id)
        ec2_res.create_tags(Resources=[instance_id], Tags=[
            {
                'Key': 'Name',
                'Value': '{}{}'.format(APP_TIER_PREFIX, j),
            },
        ])


def terminate_instance(instance_id):
    ids = []
    ids.append(instance_id)
    ec2_res.instances.filter(InstanceIds=ids).terminate()

