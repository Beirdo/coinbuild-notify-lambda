import sys
sys.path.insert(0, 'package/')
import json
import requests
import os
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)
    
notify_phases = ["QUEUED", "BUILD", "COMPLETED", "FAILED"]

status_colors = {
    "FAILED": 0xFF0000,
    "IN PROGRESS": 0x0000FF,
    "SUCCEEDED": 0x00FF00,
}

default_avatar_url = 'https://a0.awsstatic.com/libra-css/images/logos/aws_logo_smile_1200x630.png'
default_username = 'BuildBot'


def parse_service_event(event):
    source = event.get("source", None)

    if source == "aws.codepipeline":
        return parse_codepipeline_event(event)
    elif source == "aws.codebuild":
        return parse_codebuild_event(event)


def parse_codebuild_event(event):
    print(event)
    detail = event.get("detail", {})
    phase = event.get("current-phase", None)
    if phase is None:
        phase = detail.get("completed-phase", None)
    logger.info("Phase: %s" % phase)
    if phase not in notify_phases:
        return None

    additional = detail.get("additional-information", {})
    envvars = additional.get("environment", {}).get("environment-variables", [])
    envvars = {item.get("name", None): item.get("value", None) for item in envvars}
    build_type = envvars.get("BUILD", None)

    phases = additional.get("phases", [])
    phases = {item.get("phase-type", None): item for item in phases}
    
    status = detail.get("build-status", None)
    if not status:
        status = detail.get("completed-phase-status", "IN PROGRESS")
    
    if phase == "QUEUED" and status == "SUCCEEDED":
        phase = "BUILD"
        status = "IN PROGRESS"
    
    items = []
    items.append(
        {
            'name': "Project",
            'value': detail.get("project-name", "Unknown"),
            'inline': True,
        })
        
    if build_type:
        items.extend(
            [
                {
                    'name': "Build Type",
                    'value': build_type,
                    'inline': True,
                },
                {
                    'name': "Architecture",
                    'value': envvars.get("ARCH", "Unknown"),
                    'inline': True,
                }
            ])

        items.extend(
            [
                {
                    'name': "Build Number",
                    'value': int(additional.get("build-number", -1.0)),
                    'inline': True,
                },
                {
                    'name': 'Status',
                    'value': status,
                    'inline': True,
                },
                {
                    'name': 'Phase',
                    'value': phase,
                    'inline': True,
                }
            ])

    build_phase = phases.get("BUILD", {})
    if build_phase.get("end-time", None):
        build_time = build_phase.get("duration-in-seconds", None)
        if build_time is not None:
            items.append(
                {
                    'name': "Build Time (s)",
                    'value': build_time,
                    'inline': True,
                })

    return items, status

        
def parse_codepipeline_event(event):
    detail = event.get("detail", {})
    status = detail.get("state", "Unknown")
    items = [
        {
            'name': 'Pipeline',
            'value': detail.get("pipeline", "Unknown"),
            "inline": True,
        },
        {
            'name': 'Status',
            'value': status,
            "inline": True,
        },
    ]
    
    stage = detail.get("stage", None)
    if stage:
        items.append(
            {
                'name': 'Stage',
                'value': stage,
                "inline": True,
            })
        
    action = detail.get("action", None)
    if action:
        items.append(
            {
                'name': 'Action',
                'value': action,
                "inline": True,
            })
        
    return items, status



def lambda_handler(event, context):
    webhook_url = os.getenv("WEBHOOK_URL")
    username = os.getenv("BOT_USERNAME", default_username)
    avatar_url = os.getenv("BOT_AVATAR", default_avatar_url)
    
    if not webhook_url or not username or not avatar_url:
        return
    
    for record in event.get('Records', []):
        sns_message = json.loads(record['Sns']['Message'])
        try:
            parsed_message = parse_service_event(sns_message)
            if not parsed_message:
                continue
            fields, status = parsed_message
        except Exception as e:
            logger.error("Exception: %s" % e)
            continue
        
        color = status_colors.get(status, 0xCCCCCC)

        discord_data = {
            'username': username,
            'avatar_url': avatar_url,
            'embeds': [{
                'color': color,
                'fields': fields,
            }]
        }
        logging.info("Discord message: %s" % discord_data)

        headers = {'content-type': 'application/json'}
        response = requests.post(webhook_url, data=json.dumps(discord_data),
                                 headers=headers)

        logging.info(f'Discord response: {response.status_code}')
        logging.info(response.content)
        