#!/usr/bin/env python
# coding: utf-8
"""
Meraki library for device management
__status__ = "Prototype"
__author__ = "guillain.sanchez@dimensiondata.com"
"""
import json
import logging
import os
from functools import wraps
from urllib.parse import urljoin

import requests


# Decorator checking if the network is already identified
def check_network(func):
    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        if args[0] and args[0] not in cls.networks:
            cls.networks = cls.get_networks()
        if args[0] and args[0] not in cls.networks:
            return
        return func(cls, *args, **kwargs)
    return wrapper


class Meraki:
    """
    Class for simple Meraki object to provide easy method
    """

    def __init__(self, token, base_url, organization_name):
        """
        Initialize logging, proxies and Meraki settings
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

        # Meraki settings
        self.token = token
        self.base_url = base_url
        self.organization_id = self.get_organization_id(organization_name)
        self.networks = self.get_networks()

    def __repr__(self) -> str:
        return "{} - {}".format(self.base_url, self.organization_id)

    def get_networks(self) -> dict:
        """
        Get all the organization networks

        :return: A dictionary {name: id} of the organization networks
        """
        status, res = self.request("GET", "organizations/{}/networks".format(self.organization_id))
        if status == requests.codes.ok:
            return {rec['name']: rec['id'] for rec in res}

    # Functions
    def get_organization_id(self, organization_name) -> str:
        """
        Get the organization identifier

        :param organization_name: Name of the organization
        :return: Id of the organization
        """
        status, res = self.request("GET", "organizations")
        if status == requests.codes.ok:
            for rec in res:
                if rec['name'] == organization_name:
                    return rec['id']

    def request(self, action, path, data=None) -> tuple:
        """
        Wrapper function to execute formatted HTTP requests

        :param action: HTTP action (GET, POST, PUT, DELETE, ...)
        :param path: Path which will be joined to the url
        :param data: Data to send in a POST/PUT request
        :return: A tuple of the request status code and the resulting json if existing
        """
        headers = {
            'X-Cisco-Meraki-API-Key': self.token,
            'Cache-Control': "no-cache",
            "Content-Type": "application/json",
        }
        r = requests.request(action, urljoin(self.base_url, path), headers=headers, proxies=self.proxies, data=data)
        log_data = ""
        if data:
            log_data = " Data:\n{}".format(json.dumps(json.loads(data), indent=4))
        logging.info("%s request to %s returned status code %s.%s", action, r.url, r.status_code, log_data)
        try:
            return r.status_code, r.json()
        except json.decoder.JSONDecodeError:
            return r.status_code, None

    # API features
    @check_network
    def get_devices(self, network=None, serial=None) -> list:
        """
        Get devices matching some parameters

        :param network: Network name
        :param serial: Serial of the device
        :return: List of dictionaries describing devices
        """
        if network:
            if serial:
                # When requesting one device, returns a list with this device for uniformity
                res = []
                status, dic = self.request("GET", "networks/{}/devices/{}".format(self.networks[network], serial))
                res.append(dic)
            else:
                # Request all devices of a network
                status, res = self.request("GET", "networks/{}/devices".format(self.networks[network]))
        else:
            status = None
            res = []
            for network_id in self.networks.values():
                # When requesting all devices, concatenate all devices from each network
                _status, _res = self.request("GET", "networks/{}/devices".format(network_id))
                res.extend(_res)
                if _status == requests.codes.ok:
                    # If at at least one request is successful, status will be ok
                    status = requests.codes.ok
        if status == requests.codes.ok:
            return res

    @check_network
    def create_device(self, network, serial, data) -> int:
        """
        Claim and update a device

        :param network: Network name
        :param serial: Serial of the device
        :param data: Dictionary of the device attributes
        :return: Status code 201 if successful, Status code of the request otherwise
        """
        status, _ = self.request(
            "POST",
            "networks/{}/devices/claim".format(self.networks[network]),
            json.dumps({'serial': serial})
        )
        if status not in (requests.codes.created, requests.codes.ok):
            return status

        put_status = self.update_device(network, serial, data)
        if put_status == requests.codes.ok:
            return requests.codes.created
        else:
            return put_status

    @check_network
    def update_device(self, network, serial, data) -> int:
        """
        Update a device

        :param network: Network name
        :param serial: Serial of the device
        :param data: Dictionary of the device attributes
        :return: Status code of the request
        """
        status, _ = self.request(
            "PUT",
            "networks/{}/devices/{}".format(self.networks[network], serial),
            json.dumps(data)
        )
        return status

    @check_network
    def remove_device(self, network, serial) -> int:
        """
        Remove a device from a network

        :param network: Network name
        :param serial: Serial of the device
        :return: Status code of the request
        """
        status, _ = self.request(
            "POST",
            "networks/{}/devices/{}/remove".format(self.networks[network], serial)
        )
        return status
