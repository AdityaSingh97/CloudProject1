#libraries to import
import socket
import logging
import boto3
from botocore.exceptions import ClientError
import json
import time

#create client for ec2
ec2_client=boto3.client('ec2',region_name='us-east-1')
ec2_resrc=boto3.resource('ec2',region_name='us-east-1')

#create client for queue
sqs_client=boto3.client('sqs')
sqs_resrc=boto3.resource('sqs')

#define constants
#TODO add key pair and security group ID
APP_TIER_PREFIX='app_tier_ec2'
MAX_APP_EC2=19
KEY_PAIR=0
SEC_GROUP_ID=0

#launch ec2 instances
#TODO check --> min=1 required? 
#TODO check if img_id needs to be defined to 'ami=...'
def create_instance(key_pair,security_group_id,img_id,min,max):
    instance_list=ec2_resrc.create_instances(
        ImageID=img_id,
        MinCount=min,
        MaxCount=max,
        InstanceType='t2-micro',
        KeyName=key_pair,
        SecurityGroupIds=[security_group_id]
        #need to insert bash script which automates the start of app tier
    )
    #create instance tags for each instance by storing values as {'app-tier-ec2',instance number} until we arrive at 19 instances
    for i in range(max):
        j=i+1
        inst_id=instance_list[i]
        print(inst_id)
        ec2_resrc.create_tags(Resources=[inst_id],
                              Tags=[{
                                  'Key':'app-tier-ec2',
                                  'Value':'{}{}'.format(APP_TIER_PREFIX,j)
                                    }
                                ]
                              )
    
    #terminate instance 
    #add instance id of instance to be terminated into an empty array 
    #filter function from boto3 requires passing an array of instance IDs
    def terminate_instance(inst_id):
        id_list=[]
        id_list.append(inst_id)
        ec2_resrc.instances.filter(InstanceIds=id_list).terminate()
        
    #autoscaling function
    #to check get_queue_attributes function parameters 
    #TODO check if get_one_queue_attribute() function can be used from app-helper.py
    def autoscale(url):
        #get length of queue with url given, which denotes the number of req on the SQS
        queue_approx_num_msgs=sqs_client.get_queue_attributes(QueueUrl=url,AttributeNames='ApproximateNumberOfMessages')['Attributes']
        #convert to integer
        queue_len=int(queue_approx_num_msgs)
        #get number of running ec2 instances
        num_running_instances=get_running_instances()
        
        #launch 19-number of running instances
        max_ec2_launch=MAX_APP_EC2-num_running_instances
        #take the minimum of number of requests and value calculated above
        num_ec2_launch=min(queue_len,max_ec2_launch)
        #create as many instances as calculated
        create_instance(KEY_PAIR,SEC_GROUP_ID,'ami-0bb1040fdb5a076bc',min=num_ec2_launch,max=num_ec2_launch)
    
    #function to get the number of running instances
    def get_running_instances():
        instances_run=ec2_resrc.instances.filter(
            Filters=[{'Name':'instance-state-name','Values':['running']}])
        instance_ids=[]
        for instance in instance_ids:
            instance_ids.append(instance)
        return len(instance_ids)
        
    