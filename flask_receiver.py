#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2019 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

__author__ = "Gabriel Zapodeanu TME, ENB"
__email__ = "gzapodea@cisco.com"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2019 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

import requests
import urllib3
import sys
import json
import datetime
import os
import time

from flask import Flask, request, abort, send_from_directory
from flask_basicauth import BasicAuth


from urllib3.exceptions import InsecureRequestWarning  # for insecure https warnings

import wireless_teams_bot

from config import WEBHOOKD_BOT_AUTH, WEBEX_TEAMS_URL, WEBHOOKD_TEAMS_ROOM, WEBHOOKD_BOT_ID
from config import WEBHOOK_USERNAME, WEBHOOK_PASSWORD, WEBHOOK_URL

from config import WIRELESS_FOLDER

os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/

urllib3.disable_warnings(InsecureRequestWarning)  # disable insecure https warnings


app = Flask(__name__)

app.config['BASIC_AUTH_USERNAME'] = WEBHOOK_USERNAME
app.config['BASIC_AUTH_PASSWORD'] = WEBHOOK_PASSWORD
# app.config['BASIC_AUTH_FORCE'] = True  # enable if all API endpoints support HTTP basic auth

basic_auth = BasicAuth(app)


@app.route('/')  # create a homepage for testing the flask framework
@basic_auth.required
def index():
    return '<h1>Flask Receiver App is Up!</h1>', 200


@app.route('/wireless_clients', methods=['POST'])  # API endpoint to receive the wireless client into for users
@basic_auth.required
def wireless_clients():
    if request.method == 'POST':
        print('Wireless Clients Data Received')
        webhook_json = request.json

        # print the received notification
        print('Payload: ')
        print(webhook_json)

        wireless_filename = webhook_json['username'] + '.json'
        # save to a file, create new file if not existing, append to existing file
        with open(WIRELESS_FOLDER + '/' + wireless_filename, 'w') as filehandle:
            filehandle.write('%s\n' % json.dumps(webhook_json))

        return 'Wireless Clients Data Received', 202
    else:
        return 'Method not supported', 405


@app.route('/wireless_teams', methods=['POST'])  # Webhook for Webex Teams Bot for wireless client notification
def wireless_client_webhook():
    if request.method == 'POST':
        print('Wireless Teams Webhook Received')
        webhook_json = request.json

        # print the received notification
        print('Payload: ')
        print(webhook_json)

        # save to a file, create new file if not existing, append to existing file
        with open(WIRELESS_FOLDER + '/wireless_teams_detailed.log', 'a') as filehandle:
            filehandle.write('%s\n' % json.dumps(webhook_json))

        # send the message to the bot function
        status = wireless_teams_bot.message_handler(webhook_json)
        return 'Webhook Received', 202
    else:
        return 'Method not supported', 405


if __name__ == '__main__':
    app.run(debug=True)
