# The Rock Alexa skill was created so you too can smell what The Rock is cooking in AWS

import boto3
import json

# Initializing all that boto3 goodness
ec2 = boto3.resource('ec2', region_name="ap-southeast-2")
r53 = boto3.client('route53')
ecs = boto3.client('ecs', region_name="ap-southeast-2")
ssm = boto3.client('ssm', region_name="ap-southeast-2")
ddb = boto3.client('dynamodb', region_name="ap-southeast-2")
s3 = boto3.resource('s3')

# Variables, here is where I define Alex custom responses as well as userdata
SKILL_NAME = "The Rock Web Server"
DEFAULT_REPLY = '<speak><audio src="insert s3 mp3 file: Requirements MPEG v2, bit rate 48 kbps, sample rate 16000 Hz" /> </speak>'
REPLY = '<speak>Hello Mr Rock, this is Alexa. Can you please build a EC2 web server now? <break time="1s"/><audio src="insert s3 mp3 file: Requirements MPEG v2, bit rate 48 kbps, sample rate 16000 Hz" /> <break time="1s"/>..it sounds like The Rock is cooking up our web server. Lets give The Rock a minute and sample his cooking by browsing to website.... therock ....dot.... sander ....dot.... training </speak>'
CONTAINER_REPLY = '<speak> Hello Mr Rock, are you still there? <break time="1s"/><audio src="insert s3 mp3 file: Requirements MPEG v2, bit rate 48 kbps, sample rate 16000 Hz" /> <break time="1s"/>....welcome back Mr Rock.  Did you start the container? <audio src="insert s3 mp3 file: Requirements MPEG v2, bit rate 48 kbps, sample rate 16000 Hz" /> ..containers start quickly, lets browse to the website... the rock ....dot .... sander .... dot .... training ....and sample The Rocks cooking</speak>'
DATA = '#!/bin/bash\nsudo yum install -y httpd\nsudo systemctl start httpd\nsudo systemctl enable httpd\ncd /var/www/html\nsudo wget https://s3-ap-southeast-2.amazonaws.com/aws-class-demos/Alexa+Media/therock.tar.gz\nsudo tar --strip-components=1 -zxf therock.tar.gz'
CONTAINER_START_REPLY = '<speak>  Container Started </speak>'
CONTAINER_STOP_REPLY = '<speak>  Container Stopped </speak>'
DYNAMODB_REPLY='<speak> The Rock has populated our Database </speak>'


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


# Function builds an EC2 instance launched with userdata
# Also dynamically update R53 A record.  I found when I used EIP had to wait for instance to become running which would delay Alexa response up to 30+ seconds

def build_web_server():
    instances = ec2.create_instances(
        ImageId='insert custom AMI ID here', InstanceType='t2.micro', MinCount=1, MaxCount=1, UserData=DATA,
        KeyName='veenss',
        IamInstanceProfile={
            'Name': 'AlexaEC2RockDemo'
        },
        NetworkInterfaces=[{'SubnetId': 'insert subnet id', 'DeviceIndex': 0, 'AssociatePublicIpAddress': True,
                            'Groups': ['insert security group id', 'insert security group id']}],
        TagSpecifications=[
            {'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Web Server - Launched by Alexa'}, ]}, ],
    )

    instance_id = instances[0].instance_id
    ec2instance = ec2.Instance(instance_id)
    publicip = ec2instance.public_ip_address

    r53.change_resource_record_sets(
        HostedZoneId='insert R53 Hosted Zone',
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': 'insert your DNS A record',
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
        taskDefinition='insert ECS Task Definition ARN'
    )

    taskarn = task['tasks'][0]['taskArn']
    ssm.put_parameter(
        Name='ECSTaskArn',
        Value=taskarn,
        Type='String'
    )

    r53.change_resource_record_sets(
        HostedZoneId='insert R53 Hosted Zone',
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': 'insert your DNS A record',
                        'Type': 'A',
                        'TTL': 1,
                        'ResourceRecords': [{'Value': "insert public ip"}]
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
        taskDefinition='insert ECS Task Definition ARN'
    )

    taskarn = task['tasks'][0]['taskArn']
    ssm.put_parameter(
        Name='ECSTaskArn',
        Value=taskarn,
        Type='String'
    )

    r53.change_resource_record_sets(
        HostedZoneId='insert your DNS A record',
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': 'insert your DNS A record',
                        'Type': 'A',
                        'TTL': 1,
                        'ResourceRecords': [{'Value': "insert public Ip"}]
                    }
                }
            ]
        }
    )

    cardcontent = CONTAINER_START_REPLY
    speechOutput = CONTAINER_START_REPLY
    return response(speech_response_with_card(SKILL_NAME, speechOutput,
                                              cardcontent, True))


# Function stops an ECS Task without the theatrics

def stop_container():
    taskarn = ssm.get_parameter(Name='ECSTaskArn')
    taskarn = taskarn['Parameter']['Value']

    task_stop = ecs.stop_task(
        cluster='insert cluster id',
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
    s3.Bucket("insert s3 bucket").download_file("insert json list", "insert json list")
    with open('insert json list') as json_file:
        data = json.load(json_file)
        for p in data['insert DynamoDB table name']:
            Title = p['PutRequest']['Item']['Title']
            ddb.put_item(
                TableName = 'insert DynamoDB table name',
                Item = p['PutRequest']['Item']
            )
            
    cardcontent = DYNAMODB_REPLY
    speechOutput = DYNAMODB_REPLY
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
