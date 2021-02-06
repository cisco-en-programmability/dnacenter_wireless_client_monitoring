#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Copyright (c) 2020 Cisco and/or its affiliates.

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
__copyright__ = "Copyright (c) 2020 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"


import requests
import urllib3
import json
import os
import time
import datetime
import logging
import dnacentersdk

from urllib3.exceptions import InsecureRequestWarning  # for insecure https warnings

os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/

from requests.auth import HTTPBasicAuth  # for Basic Auth
from datetime import datetime

from config import DNAC_URL, DNAC_PASS, DNAC_USER
from config import CLIENT_USERNAME, CLIENT_MAC
from config import BW_LOW, HEALTH_LOW, COUNTER_MAX, TIME_INTERVAL, SNR
from config import BOT_TOKEN, WEBEX_SPACE, WEBEX_TEAMS_URL
from dnacentersdk import DNACenterAPI

urllib3.disable_warnings(InsecureRequestWarning)  # disable insecure https warnings

DNAC_AUTH = HTTPBasicAuth(DNAC_USER, DNAC_PASS)


def pprint(json_data):
    """
    Pretty print JSON formatted data
    :param json_data: data to pretty print
    :return:
    """
    print(json.dumps(json_data, indent=4, separators=(' , ', ' : ')))


def get_epoch_time():
    """
    This function will return the epoch time for current time
    :return: epoch time including msec
    """
    epoch = time.time()*1000
    return int(epoch)


def get_room_id(room_name):
    """
    This function will find the Webex Teams space id based on the {space_name}
    Call to Webex Teams - /rooms
    :param room_name: The Webex Teams room name
    :return: the Webex Teams room Id
    """
    room_id = None
    url = WEBEX_TEAMS_URL + '/v1/rooms' + '?sortBy=lastactivity&max=1000'
    header = {'content-type': 'application/json', 'authorization': BOT_TOKEN}
    space_response = requests.get(url, headers=header, verify=False)
    space_list_json = space_response.json()
    space_list = space_list_json['items']
    for spaces in space_list:
        if spaces['title'] == room_name:
            room_id = spaces['id']
    return room_id


def post_room_card_message(card_message):
    """
    This function will post a adaptive card message {card_message} to the Webex Teams space with the {space_name}
    :param card_message: card message
    :return: none
    """
    url = WEBEX_TEAMS_URL + '/messages'
    header = {'content-type': 'application/json', 'authorization': BOT_TOKEN}
    requests.post(url, data=json.dumps(card_message), headers=header, verify=False)


def main():
    """
    This application will monitor a wireless user client device.
    It will identify when the client experiences poor performance:
     - decreased total transmit and receive data
     - lower client health score
     - low SNR value
    If any of the above conditions are true, exceeding a predefined number of consecutive polling intervals,
    it will create a notification to Webex Teams
    """

    # logging, debug level, to file {application_run.log}
    logging.basicConfig(
        filename='application_run.log',
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print('\nWireless Client Monitoring App Start, ', current_time)

    print('\nWireless client user to be monitored: ', CLIENT_USERNAME)

    # Create a DNACenterAPI "Connection Object"
    dnac_api = DNACenterAPI(username=DNAC_USER, password=DNAC_PASS, base_url=DNAC_URL, version='2.1.2', verify=False)

    # If client MAC Address not found, continue with pre-configured MAC Address

    all_client_info = dnac_api.clients.get_client_enrichment_details(headers={'entity_type': 'network_user_id', 'entity_value': CLIENT_USERNAME})
    client_mac = ''
    if all_client_info != []:
        for client in all_client_info:
            if client['userDetails']['hostType'] == 'WIRELESS':
                client_mac = client['userDetails']['id']
    else:
        print('\nUnknown wireless client MAC Address for the client with the username: ', CLIENT_USERNAME)

    if client_mac == '':
        print('Wireless client MAC address not found, use the pre-configured MAC Address: ', CLIENT_MAC)
        client_mac = CLIENT_MAC
    else:
        print('\nWireless Client MAC Address found: ', client_mac, '\n')

    # start to collect data about the monitored client
    # poll the client until notification will be sent ot Webex

    alert_count = 0  # used to count when minimum performance params are not met

    while alert_count < COUNTER_MAX:

        # initialize the alert flag, used to identify if any conditions of client poor performance are met
        alert = False

        # create a DNACenterAPI "Connection Object", to avoid token expiration after 60 minutes
        dnac_api = DNACenterAPI(username=DNAC_USER, password=DNAC_PASS, base_url=DNAC_URL, version='2.1.2',
                                verify=False)

        # find out the epoch time msec
        timestamp = get_epoch_time()

        # receive the client detail info for the client with the MAC address at a specific timestamp
        client_info = dnac_api.clients.get_client_detail(mac_address=client_mac, timestamp=timestamp)

        # parse the total data transfer, ap name, snr, data rate, location, ssid
        try:
            health_score = client_info['detail']['healthScore']
            for score in health_score:
                if score['healthType'] == 'OVERALL':
                    client_health = score['score']
            total_data_transfer = float(client_info['detail']['txBytes']) + float(client_info['detail']['rxBytes'])
            ap_name = client_info['detail']['clientConnection']
            snr = float(client_info['detail']['snr'])
            data_rate = float(client_info['detail']['dataRate'])
            location = client_info['detail']['location']
            ssid = client_info['detail']['ssid']
            print(client_health, total_data_transfer, data_rate, snr, ssid, ap_name, location)
        except:
            print('\nUnable to collect the client info, client not in the Cisco DNA Center inventory')

        # verify client connectivity performance
        if client_health <= HEALTH_LOW:
            alert = True
        if snr <= SNR:
            alert = True
        if total_data_transfer <= BW_LOW:
            alert = True

        # if any of the above conditions are true, increase the alert_count
        # if performance improved during this poll interval, reset the alert_count
        if alert:
            alert_count += 1
        else:
            alert_count = 0
        print('Alert: ', alert, alert_count)
        time.sleep(TIME_INTERVAL * 60)

    # send notifications to Webex Teams

    # find the Webex Teams space id
    space_id = get_room_id(WEBEX_SPACE)

    card_message = {
        "roomId": space_id,
        "markdown": "Wireless Client Notification",
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
                            "text": "Wireless Client Notification",
                            "weight": "bolder",
                            "size": "large"
                        },
                        {
                            "type": "TextBlock",
                            "text": "Cisco DNA Center identified low wireless performance for this client:",
                            "wrap": True
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {
                                    "title": "Username: ",
                                    "value": CLIENT_USERNAME
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
                                    "title": "Total data:",
                                    "value": str(total_data_transfer)
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
                        #{
                        #    "type": "Action.openURL",
                        #    "title": "ServiceNow incident " + issue_number,
                        #    "url": jira_issue_url
                        #}
                    ]
                }
            }
        ]
    }

    post_room_card_message(card_message)

    print('Webex Teams notification message posted')

    current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print('\nWireless Client Monitoring App Run End, ', current_time)


if __name__ == '__main__':
    main()
