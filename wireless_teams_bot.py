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

import json
import os
import time

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning  # for insecure https warnings

from config import DNAC_URL
from config import WHATSOP_BOT_AUTH, WEBEX_TEAMS_URL, WHATSOP_ROOM, WHATSOP_BOT_ID
from config import WIRELESS_FOLDER
from config import WHATSOP_ROOM

os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/

urllib3.disable_warnings(InsecureRequestWarning)  # disable insecure https warnings


def message_handler(teams_message):
    """
    This function will process all the messages addressed to the bot.
    It will:
     - find the Webex Teams message id
     - read the message from teams
     - respond to the message
    :param teams_message: the initial notifications message the bot is informed there is a new message
    :return: status of the message process engine
    """
    # parse and select the message id
    message_id = teams_message['data']['id']
    message_info = get_bot_message_by_id(message_id, WHATSOP_BOT_ID)
    print('Teams message content: ' + str(message_info))
    if str.lower(message_info) in ["whatsop help", "whatsop manage"]:  # convert the message to lower case
        post_menu = '<p>I can help you with: <br/><strong>client status</strong> - Enter @WhatsOp + wireless username + status'
        post_room_markdown_message(WHATSOP_ROOM, post_menu)
    elif 'status' in str.lower(message_info):
        username = message_info.split(' ')[1]

        # attempt to open the file with the user name, if not available, reply user not found
        try:
            with open(WIRELESS_FOLDER + '/' + username + '.json', 'r') as filehandle:
                user_txt = filehandle.read()
                user_info = json.loads(user_txt)

                # parse the user data
                client_mac = user_info['details']['mac_address']
                location = user_info['details']['location']
                ap_name = user_info['details']['access_point']
                ssid = user_info['details']['ssid']
                client_health = user_info['details']['health_score'][0]['score']
                snr = user_info['details']['snr']
                timestamp = user_info['details']['timestamp']

                # prepare card message
                # find the Webex Teams space id
                space_id = get_room_id(WHATSOP_ROOM)

                card_message = {
                    "roomId": space_id,
                    "markdown": "Wireless Client Status",
                    "attachments": [
                        {
                            "contentType": "application/vnd.microsoft.card.adaptive",
                            "content": {
                                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                                "type": "AdaptiveCard",
                                "version": "1.0",
                                "body": [
                                    {
                                        "type": "TextBlock",
                                        "text": "Wireless Client Status",
                                        "weight": "bolder",
                                        "size": "large"
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": "Last collected status for this client, " + str(timestamp) + ":",
                                        "wrap": True
                                    },
                                    {
                                        "type": "FactSet",
                                        "facts": [
                                            {
                                                "title": "Username: ",
                                                "value": username
                                            },
                                            {
                                                "title": "MAC Address:",
                                                "value": client_mac
                                            },
                                            {
                                                "title": "Location:",
                                                "value": location
                                            },
                                            {
                                                "title": "Access Point:",
                                                "value": ap_name
                                            },
                                            {
                                                "title": "SSID:",
                                                "value": ssid
                                            },
                                            {
                                                "title": "Health Score:",
                                                "value": str(client_health)
                                            },
                                            {
                                                "title": "SNR:",
                                                "value": str(snr)
                                            }
                                        ]
                                    }
                                ],
                                "actions": [
                                    {
                                        "type": "Action.openURL",
                                        "title": "Cisco DNA Center Client 360",
                                        "url": DNAC_URL + '/dna/assurance/client/details?macAddress=' + client_mac
                                    }
                                ]
                            }
                        }
                    ]
                }

                post_room_card_message(card_message)

        except:
            # file not found for user post teams message
            post_menu = '<p>No data was collected for this user: <br/><strong>' + username + '</strong>'
            post_room_markdown_message(WHATSOP_ROOM, post_menu)
    else:
        post_menu = '<p>I can help you with: <br/><strong>client status</strong> - Enter wireless username + " status"'
        post_room_markdown_message(WHATSOP_ROOM, post_menu)


def get_bot_message_by_id(message_id, bot_id):
    """
    This function will get the message content using the {message_id}
    :param message_id: Webex Teams message_id
    :param bot_id: the Bot id to validate message
    :return: message content
    """
    url = WEBEX_TEAMS_URL + '/messages/' + message_id
    header = {'content-type': 'application/json', 'authorization': WHATSOP_BOT_AUTH}
    response = requests.get(url, headers=header, verify=False)
    response_json = response.json()
    all_people = response_json['mentionedPeople']
    for people in all_people:
        if people == bot_id:
            return response_json['text']
    return None


def post_room_markdown_message(space_name, message):
    """
    This function will post a markdown {message} to the Webex Teams space with the {space_name}
    Call to function get_space_id(space_name) to find the space_id
    Followed by API call /messages
    :param space_name: the Webex Teams space name
    :param message: the text of the markdown message to be posted in the space
    :return: none
    """
    space_id = get_room_id(space_name)
    payload = {'roomId': space_id, 'markdown': message}
    url = WEBEX_TEAMS_URL + '/messages'
    header = {'content-type': 'application/json', 'authorization': WHATSOP_BOT_AUTH}
    requests.post(url, data=json.dumps(payload), headers=header, verify=False)


def get_room_id(room_name):
    """
    This function will find the Webex Teams space id based on the {space_name}
    Call to Webex Teams - /rooms
    :param room_name: The Webex Teams room name
    :return: the Webex Teams room Id
    """
    room_id = None
    url = WEBEX_TEAMS_URL + '/rooms' + '?max=1000'
    header = {'content-type': 'application/json', 'authorization': WHATSOP_BOT_AUTH}
    space_response = requests.get(url, headers=header, verify=False)
    space_list_json = space_response.json()
    space_list = space_list_json['items']
    for spaces in space_list:
        if spaces['title'] == room_name:
            room_id = spaces['id']
    return room_id


def post_room_message(space_name, message):
    """
    This function will post the {message} to the Webex Teams space with the {space_name}
    Call to function get_space_id(space_name) to find the space_id
    Followed by API call /messages
    :param space_name: the Webex Teams space name
    :param message: the text of the message to be posted in the space
    :return: none
    """
    space_id = get_room_id(space_name)
    payload = {'roomId': space_id, 'text': message}
    url = WEBEX_TEAMS_URL + '/messages'
    header = {'content-type': 'application/json', 'authorization': WHATSOP_BOT_AUTH}
    requests.post(url, data=json.dumps(payload), headers=header, verify=False)


def post_room_card_message(card_message):
    """
    This function will post a adaptive card message {card_message} to the Webex Teams space with the {space_name}
    :param card_message: card message
    :return: none
    """
    url = WEBEX_TEAMS_URL + '/messages'
    header = {'content-type': 'application/json', 'authorization': WHATSOP_BOT_AUTH}
    requests.post(url, data=json.dumps(card_message), headers=header, verify=False)
