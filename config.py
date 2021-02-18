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


# This file contains:

# Cisco DNA Center "dnalive.cisco.com"
DNAC_URL = 'cisco_dna_center'
DNAC_USER = 'admin'
DNAC_PASS = 'password'

# the wireless client info
CLIENT_USERNAME = 'username'
CLIENT_MAC = 'mac_address'

# Assurance thresholds
BW_LOW = 100.0  # in Bytes, total bandwidth transmitted and received
HEALTH_LOW = 8  # minimum health score, range 1-10
SNR = 60.0  # minimum SNR
COUNTER_MAX = 3  # number of consecutive time intervals when the quality is low to trigger alert
TIME_INTERVAL = 5  # length of time in minutes

# Webex bot info
WEBEX_TEAMS_URL = 'https://webexapis.com'
WHATSOP_BOT_AUTH = 'Bearer ' + 'token'
WHATSOP_BOT_ID = 'bot_id'
WHATSOP_ROOM = 'Wireless Clients Monitoring'

# PythonAnywhere Receiver Info
WEBHOOK_RECEIVER_URL = 'receiver_url'
WEBHOOK_HEADER = {'content-type': 'application/json', 'Authorization': 'Basic http_basic_auth'}

# Wireless clients use case
WIRELESS_FOLDER = 'wireless_clients'
