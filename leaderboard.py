import json
from botocore.vendored import requests #TO BE DEPRECATED
from urllib import parse as urlparse
import base64
from functools import lru_cache
import math
from datetime import datetime, timedelta, timezone
import sys
import boto3
import uuid
from secrets import LEADERBOARD_ID, SESSION_ID, SLACK_WEBHOOK, NAME_DEFAULT, BUCKET_NAME, SLACK_TOKEN, USER_MAP
import time

LEADERBOARD_URL = "https://adventofcode.com/{}/leaderboard/private/view/{}".format(datetime.today().year, LEADERBOARD_ID)
s3_client = boto3.client('s3')

def start(user_name, user_id, day):
    data = _get_data()
    if user_id not in USER_MAP:
        return "You must register your Advent<->Slack mapping first"
    
    advent_user = f"U_{USER_MAP[user_id]}"
    if advent_user not in data['start_times']:
        data['start_times'][advent_user] = {}

    start_time = int(time.time())
    data['start_times'][advent_user][f"day_{day}"] = start_time
    _persist_data(data)
    
    return f"Logged start time of {start_time} for {user_name} for day {day}. You may begin:\n https://adventofcode.com/2020/day/{day}"

def leaderboard(user_name, user_id, day):
    return _build_leaderboard()

def today(user_name, user_id, day):
    return _build_leaderboard(day)

def details(user_name, user_id, day):
    data = _get_data()
    return json.dumps(data)


commands = {'start':start,
            'leaderboard':leaderboard,
            'details': details,
            'today': today,
} 


def lambda_handler(event, context):

    msg_params = dict(urlparse.parse_qsl(base64.b64decode(str(event['body'])).decode('ascii')))
    if msg_params.get('token') != SLACK_TOKEN:
        return "Invalid token"

    command = msg_params.get('command','err') 
    params = msg_params.get('text','None').split(" ") 
    subcommand = params[0].lower()
    today = datetime.now(timezone.utc) - timedelta(hours=5, minutes=0)# Unlock time is midnight UTC-5
    user_name = msg_params.get('user_name','')
    user_id = msg_params.get('user_id','')
    if (subcommand in commands.keys()):
        response = commands[subcommand](user_name, user_id, today.day)
    elif subcommand == 'none':
        response = f"Available commands are {list(commands.keys())}"
    else:
        response = f'Illegal command "{subcommand}". Available commands are: {list(commands.keys())}'


    return  {
        "response_type": "in_channel",
        "text": command + ' ' + " ".join(params),
        "attachments": [
            {
                "text": response
            }
        ]
    }
  
  
def _formatLeaderMessage(members, day):
    """
    Format the message to conform to Slack's API
    """
    message = ""

    # add each member to message
    medals = [':third_place_medal:', ':second_place_medal:', ':trophy:']
    for username, score, stars, completion_time in members:
        if medals:
            medal = ' ' + medals.pop()
        else:
            medal = ''
        if day:
            message += f"{medal}*{username}* Today's Time: {str(timedelta(seconds=completion_time))} \n"
        else:
            message += f"{medal}*{username}* {stars} Stars. \n"

    message += f"\n<{LEADERBOARD_URL}|View Leaderboard Online>"

    return message


def _parseMembers(mj, day, data):
    if day:
        start_of_today = 1606712400 + day*(60*60*24) #2020 hardcoded for now
    else:
        start_of_today = 0
    members = []
    
    for k in mj.keys():
        recent_star_ts = mj[k]["completion_day_level"].get(str(day), {}).get("2",{}).get("get_star_ts", 2*start_of_today)
        today_start_ts = data['start_times'].get(f"U_{k}", {}).get(f"day_{day}", start_of_today)
        new_tup = (mj[k].get("name") or NAME_DEFAULT,
                    mj[k]["local_score"],
                    mj[k]["stars"],
                    int(recent_star_ts) - int(today_start_ts)
                )
        members.append(new_tup)


    # sort members by score, descending
    if day:
        members.sort(key=lambda s: (s[3], -s[2], -s[1]))
    else:
        members.sort(key=lambda s: (-s[2], -s[1]))

    return members


def _build_leaderboard(day=None):
    data = _get_data()
    # make sure all variables are filled
    if LEADERBOARD_ID == "" or SESSION_ID == "" or SLACK_WEBHOOK == "":
        return "ERROR: Some variables not initialized"

    # retrieve leaderboard
    r = requests.get(
        "{}.json".format(LEADERBOARD_URL),
        cookies={"session": SESSION_ID}
    )
    if r.status_code != requests.codes.ok: #pylint: disable=no-member
        return "Error retrieving leaderboard"

    # get members from json
    members = _parseMembers(r.json()["members"], day, data)

    # generate message to send to slack
    message = _formatLeaderMessage(members, day)
    return message


def _persist_data(data):
    local_path = '/tmp/{}'.format(uuid.uuid4())
    with open(local_path, 'w') as outfile:
        json.dump(data, outfile)
    
    s3_client.upload_file(local_path, BUCKET_NAME, 'advent.json')
    return


def _get_data():
    download_path = '/tmp/{}'.format(uuid.uuid4())
    s3_client.download_file(BUCKET_NAME, 'advent.json', download_path)
    with open(download_path) as f:
        data = json.load(f)

    if 'start_times' not in data:
        data['start_times'] = {}
        
    return data
