import sys
sys.path.insert(0, 'package/')
import json
import requests
import os
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


"""
{"account": "890058568674", "detailType": "CodePipeline Pipeline Execution State Change", "region": "us-west-2", "source": "aws.codepipeline", "time": "2021-08-15T10:19:15Z", "notificationRuleArn": "arn:aws:codestar-notifications:us-west-2:890058568674:notificationrule/2c2abf2977c16930f768b6bae4ba1adc37554d4c", "detail": {"pipeline": "WayaWolfCoin", "execution-id": "863b3f68-aab1-4744-b184-68462573160a", "execution-trigger": {"trigger-type": "StartPipelineExecution", "trigger-detail": "arn:aws:iam::890058568674:root"}, "state": "STARTED", "version": 9.0}, "resources": ["arn:aws:codepipeline:us-west-2:890058568674:WayaWolfCoin"], "additionalAttributes": {}}

{"account": "890058568674", "detailType": "CodePipeline Action Execution State Change", "region": "us-west-2", "source": "aws.codepipeline", "time": "2021-08-15T10:30:10Z", "notificationRuleArn": "arn:aws:codestar-notifications:us-west-2:890058568674:notificationrule/2c2abf2977c16930f768b6bae4ba1adc37554d4c", "detail": {"pipeline": "WayaWolfCoin", "execution-id": "863b3f68-aab1-4744-b184-68462573160a", "stage": "Build", "execution-result": {"external-execution-url": "https://console.aws.amazon.com/codebuild/home?region=us-west-2#/builds/build-batch/WayaWolfCoin:79f99f78-a79f-48e4-aa9e-4fffdbf3fc9b/view/new", "external-execution-id": "build-batch/WayaWolfCoin:79f99f78-a79f-48e4-aa9e-4fffdbf3fc9b"}, "output-artifacts": [{"name": "Output", "s3location": {"bucket": "codepipeline-us-west-2-19350903934", "key": "WayaWolfCoin/Output/geJaVBS"}}], "action": "Build", "state": "SUCCEEDED", "region": "us-west-2", "type": {"owner": "AWS", "provider": "CodeBuild", "category": "Build", "version": "1"}, "version": 9.0}, "resources": ["arn:aws:codepipeline:us-west-2:890058568674:WayaWolfCoin"], "additionalAttributes": {}}
"""

def parse_service_event(event):
    source = event.get("source", None)

    if source == "aws.codepipeline":
        return parse_codepipeline_event(event)
    elif source == "aws.codebuild":
        return parse_codebuild_event(event)
        

def parse_codebuild_event(event):
    return None

        
def parse_codepipeline_event(event):
    detail = event.get("detail", {})
    trigger = event.get("execution-trigger", {})
    
    items = [
        {
            'name': 'Pipeline',
            'value': detail.get("pipeline", "Unknown"),
            "inline": True
        },
        {
            'name': 'TriggerType',
            'value': trigger.get("trigger-type", "Unknown"),
            "inline": True
        },
        {
            'name': 'State',
            'value': detail.get("state", Unknown),
            "inline": True
        },
    ]
    
    stage = detail.get("stage", None)
    if stage:
        items.append(
            {
                'name': 'Stage',
                'value': stage,
                "inline": True
            })
        
    action = detail.get("action", None)
    if action:
        items.append(
            {
                'name': 'Action',
                'value': action,
                "inline": True
            })
        
    return items


def lambda_handler(event, context):
    webhook_url = os.getenv("WEBHOOK_URL")
    print(event)
    
    for record in event.get('Records', []):
        sns_message = json.loads(record['Sns']['Message'])
        parsed_message = parse_service_event(sns_message)
        if not parsed_message:
            continue
        
        discord_data = {
            'username': 'CoinBuilder',
            'avatar_url': 'https://a0.awsstatic.com/libra-css/images/logos/aws_logo_smile_1200x630.png',
            'embeds': [{
                'color': 16711680,
                'fields': parsed_message
            }]
        }

        headers = {'content-type': 'application/json'}
        response = requests.post(webhook_url, data=json.dumps(discord_data),
                                 headers=headers)

        logging.info(f'Discord response: {response.status_code}')
        logging.info(response.content)