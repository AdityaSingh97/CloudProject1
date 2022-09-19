#libraries to import
import socket
import logging
import boto3
from botocore.exceptions import ClientError

#create client for ec2
ec2_client=boto3.client('ec2',region_name='us-east-1')
ec2_resrc=boto3.resource('ec2',region_name='us-east-1')

#define constants


#launch ec2 instances
def create_instance(key_pair,security_group_id,img_id='ami-0bb1040fdb5a076bc'):
    instance_list=ec2_resrc.create_instances(
        ImageID=img_id,
        MinCount=1,
        MaxCount=1,
        InstanceType='t2-micro',
        KeyName=key_pair,
        SecurityGroupIds=[security_group_id]
        #need to insert bash script which automates the start of web tier
    )
    #create instance tags for each instance by storing values as {'app-tier-ec2',instance number} until we arrive at 19 instances
    for i in range(1):
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
    
    
        
    