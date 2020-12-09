# Advent of Code Leaderboard Slash Command 

This repository contains the code for a script that will run a Slash Command for a Private Advent of Code Leaderboard on Slack. This repo is a fork from tomswartz and expanded to be a slash command

For me, midnight EST is not a good time to attempt the challenges, so I've added `/advent start` as a way for users to mark their start time which results in a custom leaderboard. This of course requires participants not to cheat and peak at solutions. 

Commands:
leaderboard: display the overall leaderboard ranked by stars
today: display today's ranking ranked by how fast each partipant was (either from midnight EST, or when they used `/advent start`

## Setup
**Prerequisites**:
- Python 3
- AWS Lambda
- AWS S3


**Process**:

1. Create a new Slack Slash Command and connect to AWS Lambda I followed this tutorial https://codeburst.io/building-a-slack-slash-bot-with-aws-lambda-python-d0d4a400de37
2. Log in to Advent of Code and obtain two things: the Private Leaderboard ID Number and a Session Cookie.
See [Session Cookie](#getting-a-session-cookie) section for details.
3. Dump that info into a `secrets.py` file.
  - Webhook URL goes in the `SLACK_WEBHOOK` variable
  - Session goes in the `SESSION_ID` variable
  - Leaderboard ID goes in the `LEADERBOARD_ID` variable.
    - The ID is the last part of the leaderboard url (https://adventofcode.com/2018/leaderboard/private/view/LEADERBOARD_ID)
5. Configure AWS S3 storage to keep track of custom start times. You could also use a database or any other storage solution you prefer.
6. Add AWS configuration parameters to secrets.py
7. Deploy and try `/advent start`
