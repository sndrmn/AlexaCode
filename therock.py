# The Rock Alexa skill was created so you too can smell what The Rock is cooking in AWS

import boto3
import json
import time

# Initializing all that boto3 goodness
ec2 = boto3.resource('ec2', region_name="ap-southeast-2")
r53 = boto3.client('route53')
ecs = boto3.client('ecs', region_name="ap-southeast-2")
ssm = boto3.client('ssm', region_name="ap-southeast-2")
ssm2 = boto3.client('ssm', region_name="eu-west-2")
ddb = boto3.client('dynamodb', region_name="ap-southeast-2")
s3 = boto3.resource('s3')
cf = boto3.client('cloudformation', region_name="ap-southeast-2")
cf2 = boto3.client('cloudformation', region_name="eu-west-2")

# Variables, here is where I define Alex custom responses as well as userdata
SKILL_NAME = "The Rock Web Server"
DEFAULT_REPLY = '<speak><audio src="*****************" /> </speak>'
REPLY = '<speak><audio src="*****************" /> </speak>'
CONTAINER_REPLY = '<speak> Hello Mr Rock, are you still there? <break time="1s"/><audio src="*****************" /> <break time="1s"/>....welcome back Mr Rock.  Did you start the container? <audio src="*****************" /> ..containers start quickly, lets browse to the website... the rock ....dot .... sander .... dot .... training ....and sample The Rocks cooking</speak>'
DATA = '#!/bin/bash\nsudo yum install -y httpd\nsudo systemctl start httpd\nsudo systemctl enable httpd\ncd /var/www/html\nsudo wget *****************\nsudo tar --strip-components=1 -zxf therock.tar.gz'
CONTAINER_START_REPLY = '<speak>  Container Started </speak>'
CONTAINER_STOP_REPLY = '<speak>  Container Stopped </speak>' 
DYNAMODB_REPLY='<speak><audio src="*****************" /></speak>'
CF_REPLY='<speak><audio src="*****************" /> The Rock is launching our Cloud Formation stacks in Sydney and London, check CF console for progress </speak>'
R53_REPLY='<speak><audio src="*****************" /> The Rock has created the R53 Demo DNS records </speak>'

# Code starts here and based on type of sessions directs flow appropriately

def lambda_handler(event, context):
    if event['session']['new']:
        on_session_started()
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended()


# Here is where we process the intents that come from the Alexa Skill

def on_intent(request, session):
    intent_name = request['intent']['name']
    if intent_name == "webserver":
        return build_web_server()
    elif intent_name == "containerrock":
        return start_rockcontainer()
    elif intent_name == "containerstart":
        return start_container()
    elif intent_name == "containerstop":
        return stop_container()
    elif intent_name == "dynamoDB":
        return complete_dynamoDB()
    elif intent_name == "cloudformation":
        return cfdemo()
    elif intent_name == "DNSRecords":
        return R53Records()


# Function builds an EC2 instance launched with userdata
# Also dynamically update R53 A record.  I found when I used EIP had to wait for instance to become running which would delay Alexa response up to 30+ seconds

def build_web_server():
    instances = ec2.create_instances(
        ImageId='*****************', InstanceType='t2.micro', MinCount=1, MaxCount=1, UserData=DATA,
        KeyName='*****************',
        IamInstanceProfile={
            'Name': '*****************'
        },
        NetworkInterfaces=[{'SubnetId': '*****************', 'DeviceIndex': 0, 'AssociatePublicIpAddress': True,
                            'Groups': ['*****************', '*****************']}],
        TagSpecifications=[
            {'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Web Server - Launched by Alexa'}, ]}, ],
    )
    time.sleep(2)
    instance_id = instances[0].instance_id
    #print instance_id
    ec2instance = ec2.Instance(instance_id)
    #print ec2instance
    publicip = ec2instance.public_ip_address
    #print publicip

    r53.change_resource_record_sets(
        HostedZoneId='*****************',
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': 'therock.sander.training.',
                        'Type': 'A',
                        'TTL': 1,
                        'ResourceRecords': [{'Value': publicip}]
                    }
                }
            ]
        }
    )

    cardcontent = REPLY
    speechOutput = REPLY
    return response(speech_response_with_card(SKILL_NAME, speechOutput,
                                              cardcontent, True))


# Function starts a ECS Task with the Alexa and Rock theatrics

def start_rockcontainer():
    task = ecs.run_task(
        cluster='TheRocks-Cluster',
        taskDefinition='*****************'
    )
    
    taskarn = task['tasks'][0]['taskArn']
    ssm.put_parameter(
        Name='ECSTaskArn',
        Value=taskarn,
        Type='String'
    )

    r53.change_resource_record_sets(
        HostedZoneId='*****************',
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': 'therock.sander.training.',
                        'Type': 'A',
                        'TTL': 1,
                        'ResourceRecords': [{'Value': "*****************"}]
                    }
                }
            ]
        }
    )

    cardcontent = CONTAINER_REPLY
    speechOutput = CONTAINER_REPLY
    return response(speech_response_with_card(SKILL_NAME, speechOutput,
                                              cardcontent, True))


# Function starts an ECS Task without the theatrics
# Writes taskArn to SSM Parameter store which stop function can read to stop the ECS task if required

def start_container():
    task = ecs.run_task(
        cluster='TheRocks-Cluster',
        taskDefinition='*****************'
    )

    taskarn = task['tasks'][0]['taskArn']
    ssm.put_parameter(
        Name='ECSTaskArn',
        Value=taskarn,
        Type='String'
    )

    #r53.change_resource_record_sets(
    #    HostedZoneId='*****************',
    #    ChangeBatch={
    #        'Changes': [
    #            {
    #                'Action': 'UPSERT',
    #                'ResourceRecordSet': {
    #                    'Name': 'therock.sander.training.',
    #                    'Type': 'A',
    #                    'TTL': 1,
    #                    'ResourceRecords': [{'Value': "*****************"}]
    #                }
    #            }
    #        ]
    #    }
    #)

    cardcontent = CONTAINER_START_REPLY
    speechOutput = CONTAINER_START_REPLY
    return response(speech_response_with_card(SKILL_NAME, speechOutput,
                                              cardcontent, True))


# Function stops an ECS Task without the theatrics

def stop_container():
    taskarn = ssm.get_parameter(Name='ECSTaskArn')
    taskarn = taskarn['Parameter']['Value']

    task_stop = ecs.stop_task(
        cluster='TheRocks-Cluster',
        task=taskarn
    )

    taskarn = ssm.delete_parameter(Name='ECSTaskArn')

    cardcontent = CONTAINER_STOP_REPLY
    speechOutput = CONTAINER_STOP_REPLY
    return response(speech_response_with_card(SKILL_NAME, speechOutput,
                                              cardcontent, True))

# Function populates the dynamoDB created earlier
# DB Name = TheRockMovies, Primary Key = Year, Sort Key = Title

def complete_dynamoDB():
    s3.Bucket("*****************").download_file("MovieList.json", "/tmp/MovieList.json")
    with open('/tmp/MovieList.json') as json_file:
        data = json.load(json_file)
        for p in data['TheRockMovies']:
            Title = p['PutRequest']['Item']['Title']
            ddb.put_item(
                TableName = 'TheRockMovies',
                Item = p['PutRequest']['Item']
            )
            
    cardcontent = DYNAMODB_REPLY
    speechOutput = DYNAMODB_REPLY
    return response(speech_response_with_card(SKILL_NAME, speechOutput,
                                              cardcontent, True))

def cfdemo():
    cfinfo = cf.create_stack(
        StackName='TheRockSydney',
        TemplateURL='*****************',
        RoleARN='*****************',
        )
    cfinfo2 = cf2.create_stack(
        StackName='TheRockLondon',
        TemplateURL='*****************',
        RoleARN='*****************',
        )
    
    cardcontent = CF_REPLY
    speechOutput = CF_REPLY
    return response(speech_response_with_card(SKILL_NAME, speechOutput,
                                              cardcontent, True))

def R53Records():
    syd = ssm.get_parameter(Name='R53-Demo-ELB-DNS')
    syd = syd['Parameter']['Value']
    lon = ssm2.get_parameter(Name='R53-Demo-ELB-DNS')
    lon = lon['Parameter']['Value']
    
    # Create Failover Records x 2
    sydfailover = r53.change_resource_record_sets(
        HostedZoneId = '*****************',
        ChangeBatch = {
            'Changes': [
                {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'failover.sander.training',
                    'Type': 'A',
                    'SetIdentifier': 'RockSydney',
                    'Failover': 'PRIMARY',
                    'AliasTarget': {
                        'HostedZoneId': '*****************',
                        'DNSName': syd,
                        'EvaluateTargetHealth': True
                    }
                }
                },
            ]
        }
    )
    
    lonfailover = r53.change_resource_record_sets(
        HostedZoneId = '*****************',
        ChangeBatch = {
            'Changes': [
                {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'failover.sander.training',
                    'Type': 'A',
                    'SetIdentifier': 'RockLondon',
                    'Failover': 'SECONDARY',
                    'AliasTarget': {
                        'HostedZoneId': '*****************',
                        'DNSName': lon,
                        'EvaluateTargetHealth': True
                    }
                }
                },
            ]
        }
    )
    
    # Create Geolocation Records x 3
    defgeolocation = r53.change_resource_record_sets(
        HostedZoneId = '*****************',
        ChangeBatch = {
            'Changes': [
                {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'geolocation.sander.training',
                    'Type': 'A',
                    'SetIdentifier': 'RockDefault',
                    'GeoLocation': {
                        'CountryCode': '*'
                    },
                    'AliasTarget': {
                        'HostedZoneId': '*****************',
                        'DNSName': syd,
                        'EvaluateTargetHealth': True
                    }
                }
                },
            ]
        }
    )
    
    sydgeolocation = r53.change_resource_record_sets(
        HostedZoneId = '*****************',
        ChangeBatch = {
            'Changes': [
                {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'geolocation.sander.training',
                    'Type': 'A',
                    'SetIdentifier': 'RockSydney',
                    'GeoLocation': {
                        'ContinentCode': 'AS'
                    },
                    'AliasTarget': {
                        'HostedZoneId': '*****************',
                        'DNSName': syd,
                        'EvaluateTargetHealth': True
                    }
                }
                },
            ]
        }
    )
    
    longeolocation = r53.change_resource_record_sets(
        HostedZoneId = '*****************',
        ChangeBatch = {
            'Changes': [
                {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'geolocation.sander.training',
                    'Type': 'A',
                    'SetIdentifier': 'RockLondon',
                    'GeoLocation': {
                        'ContinentCode': 'EU'
                    },
                    'AliasTarget': {
                        'HostedZoneId': '*****************',
                        'DNSName': lon,
                        'EvaluateTargetHealth': True
                    }
                }
                },
            ]
        }
    )
    
    # Create Latency Records x 2
    sydlatency = r53.change_resource_record_sets(
        HostedZoneId = '*****************',
        ChangeBatch = {
            'Changes': [
                {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'latency.sander.training',
                    'Type': 'A',
                    'SetIdentifier': 'RockSydney',
                    'Region': 'ap-southeast-2',
                    'AliasTarget': {
                        'HostedZoneId': '*****************',
                        'DNSName': syd,
                        'EvaluateTargetHealth': True
                    }
                }
                },
            ]
        }
    )
    
    lonlatency = r53.change_resource_record_sets(
        HostedZoneId = '*****************',
        ChangeBatch = {
            'Changes': [
                {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'latency.sander.training',
                    'Type': 'A',
                    'SetIdentifier': 'RockLondon',
                    'Region': 'eu-west-2',
                    'AliasTarget': {
                        'HostedZoneId': '*****************',
                        'DNSName': lon,
                        'EvaluateTargetHealth': True
                    }
                }
                },
            ]
        }
    )
    
    # Create GeoProximity Policies & Records

    #I am not a dev :( -  this was my hack to get a variable into my JSON    
    part1 = '''
    {
        "AWSPolicyFormatVersion":"2015-10-01",
        "RecordType":"A",
        "StartRule":"geoprox-rule",
        "Endpoints":{
            "aws-eu-west-2-region":{
                "Type":"elastic-load-balancer",
                "Value":'''
    part2 = '''
            },
            "aws-ap-southeast-2-region":{
                "Type":"elastic-load-balancer",
                "Value":'''
    part3 = '''
            }
        },
        "Rules":{
            "geoprox-rule":{
                "RuleType": "geoproximity",
                "GeoproximityLocations": [
                    {
                        "EndpointReference": "aws-eu-west-2-region",
                        "Region": "aws:route53:eu-west-2",
                        "Bias": "0",
                        "EvaluateTargetHealth": "true"
                    },
                    {
                        "EndpointReference": "aws-ap-southeast-2-region",
                        "Region": "aws:route53:ap-southeast-2",
                        "Bias": "0",
                        "EvaluateTargetHealth": "true"
                    }
                ]
            }
        }
    }'''
    part4 = '''
            }
        },
        "Rules":{
            "geoprox-rule":{
                "RuleType": "geoproximity",
                "GeoproximityLocations": [
                    {
                        "EndpointReference": "aws-eu-west-2-region",
                        "Region": "aws:route53:eu-west-2",
                        "Bias": "-99",
                        "EvaluateTargetHealth": "true"
                    },
                    {
                        "EndpointReference": "aws-ap-southeast-2-region",
                        "Region": "aws:route53:ap-southeast-2",
                        "Bias": "99",
                        "EvaluateTargetHealth": "true"
                    }
                ]
            }
        }
    }'''
    gp1 = (part1+'"'+lon+'"'+part2+'"'+syd+'"'+part3)
    gp2 = (part1+'"'+lon+'"'+part2+'"'+syd+'"'+part4)
    
    
    geopolicy = r53.create_traffic_policy(
        Name='R53Demo',
        Document=gp1,
        Comment='R53 Geoproximity Demo'
        )
    
    #To create V2 traffic policy we need to find the unique ID of the first policy
    geopolicyver = r53.list_traffic_policies()
    geopolicyver = geopolicyver['TrafficPolicySummaries'][0]['Id']
    
    #Here we create V2 traffic policy using BIAS towards SYD
    geopolicy2 = r53.create_traffic_policy_version(
        Id=geopolicyver,
        Document=gp2,
        Comment='R53 Geoproximity Demo with Bias'
        )
    
    #Here we create GeoProximity A record using v1 traffic policy
    geoprox1 = r53.create_traffic_policy_instance(
        HostedZoneId='*****************',
        Name='geoproximity.sander.training',
        TTL=60,
        TrafficPolicyId=geopolicyver,
        TrafficPolicyVersion=1
        )
    #Here we create GeoProximity A record using v2 traffic policy
    geoprox2 = r53.create_traffic_policy_instance(
        HostedZoneId='*****************',
        Name='geoproximity2.sander.training',
        TTL=60,
        TrafficPolicyId=geopolicyver,
        TrafficPolicyVersion=2
        )
    
    cardcontent = R53_REPLY
    speechOutput = R53_REPLY
    return response(speech_response_with_card(SKILL_NAME, speechOutput,
                                              cardcontent, True)) 

def on_session_started():
    """" called when the session starts  """
    # print("on_session_started")


def on_session_ended():
    """ called on session ends """
    # print("on_session_ended")


# I keep this here so a default sound bite plays so I know the Alexa skill is working before class
def on_launch(request):
    cardcontent = DEFAULT_REPLY
    speechOutput = DEFAULT_REPLY
    return response(speech_response_with_card(SKILL_NAME, speechOutput,
                                              cardcontent, True))


# This is where we process the Speech responses

def speech_response_with_card(title, output, cardcontent, endsession):
    return {
        'card': {
            'type': 'Simple',
            'title': title,
            'content': cardcontent
        },
        'outputSpeech': {
            'type': 'SSML',
            'ssml': output
        },
        'shouldEndSession': endsession
    }


def response(speech_message):
    return {
        'version': '1.0',
        'response': speech_message
    }
