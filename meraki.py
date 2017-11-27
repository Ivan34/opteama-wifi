#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Meraki class to drive AP deployment
__status__ = "Prototype"
__author__ = "guillain.sanchez@dimensiondata.com"
"""

import json
import logging
import os
import re
from urllib.parse import urljoin

import requests


class Meraki:
    """
    Class for simple Meraki object to provide easy method
    """

    def __init__(self, token, base_url, organization_name):
        """
        Initialize logging, proxies and basic settings
        """
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s :: %(message)s')

        # Proxy parameters
        self.proxies = None
        proxy_url = os.getenv("PROXY_URL", '').split('://')[-1]
        if proxy_url:
            user = os.getenv("PROXY_USER")
            password = os.getenv("PROXY_PASSWORD")
            if user and password:
                proxy_url = 'http://{}:{}@{}'.format(user, password, proxy_url)
            else:
                proxy_url = 'http://{}'.format(proxy_url)
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }

        # Settings
        self.token = token
        self.base_url = base_url
        self.organization_id = self.get_organization_id(organization_name)

    def __repr__(self):
        return "{} - {} - {}".format(self.token, self.base_url, self.organization_id)

    # API features
    def get_device(self, site=None, serial=None):
        if site:
            if serial:
                return self.request("GET", "networks/{}/devices/{}".format(self.get_network_id(site), serial))
            return self.request("GET", "networks/{}/devices".format(self.get_network_id(site)))
        return self.request("GET", "organizations/{}/inventory".format(self.organization_id))

    def post_device(self, serial, site, building, floor, lat=None, lon=None):
        r = self.request(
            "POST",
            "networks/{}/devices/claim".format(self.get_network_id(site)),
            json.dumps({'serial': serial})
        )
        if not r:
            return

        r = self.update_device(serial, site, building, floor, lat, lon)
        return r

    def update_device(self, serial, site, building=None, floor=None, lat=None, lon=None):
        r = self.get_device(site, serial)

        if re.match("[A-Z]{3}-AP-[A-Z]{3}-[A-Za-z0-9]*-[0-9]*", r['name']):
            _site, _AP, current_building, current_floor, index = r['name'].split('-')
            if not building:
                building = current_building
            if not floor:
                floor = current_floor
        else:
            r = self.get_device(site)
            pattern = '{}-AP-{}-{}-'.format(site, building, floor)
            index_list = [int(dic['name'][len(pattern):]) for dic in r if dic['name'].startswith(pattern)]
            if index_list:
                index = max(index_list) + 1
            else:
                index = 1

        data = {'name': '{}-AP-{}-{}-{}'.format(site, building, floor, index)}

        if lat:
            data['lat'] = lat
        if lon:
            data['lon'] = lon

        r = self.request(
            "PUT",
            "/networks/{}/devices/{}".format(self.get_network_id(site), serial),
            json.dumps(data)
        )
        return r

    def remove_device(self, site, serial):
        return self.request("POST", "networks/{}/devices/{}/remove".format(self.get_network_id(site), serial))

    # Functions
    def request(self, action, path, data=None):
        headers = {
            'X-Cisco-Meraki-API-Key': self.token,
            'Cache-Control': "no-cache",
            "Content-Type": "application/json",
        }
        r = requests.request(action, urljoin(self.base_url, path), headers=headers, proxies=self.proxies, data=data)
        if r.status_code != requests.codes.ok:
            return None
        return r.json()

    def get_network_id(self, name) -> str:
        r = self.request("GET", "organizations/{}/networks".format(self.organization_id))
        for rec in r:
            if rec['name'] == name:
                return rec['id']

    def get_organization_id(self, name) -> str:
        r = self.request("GET", "organizations")
        for rec in r:
            if rec['name'] == name:
                return rec['id']
