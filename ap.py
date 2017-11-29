#!/usr/bin/env python3
# coding: utf-8
"""
Connexion application for the API of OPTEAMA Wifi Access points
"""
import os
import re

import connexion
import flask
import requests
import yaml

from meraki import Meraki

# Meraki settings and initializing
meraki = None
api_key = os.getenv("MERAKI_API_KEY")
api_url = "https://api.meraki.com/api/v0/"
organization = "STELIA-SAS-PROD"
if not api_key:
    raise Exception("Meraki API key missing")


def init_meraki(func):
    """
    Decorator to init Meraki after the application starting
    """
    def wrapper(*args, **kwargs):
        global meraki
        if not meraki:
            meraki = Meraki(api_key, api_url, organization)
        return func(*args, **kwargs)
    return wrapper


@init_meraki
def get_aps(site=None, serial=None):
    """
    Get list of Access Points

    :param site: Site name
    :param serial: Serial of the Access Point
    :return: List of dictionaries describing access points
    """
    swagger_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'swagger.yaml')
    with open(swagger_file, 'r') as stream:
        # Read the swagger to get the list of sites
        swagger = yaml.load(stream)
        all_sites = swagger['parameters']['Site']['enum']

    if not site:
        # Get all AP in the sites defined in the swagger
        res = []
        for _site in all_sites:
            site_res = meraki.get_devices(_site, serial)
            if site_res:
                for ap in site_res:
                    ap['site'] = _site
                res.extend(site_res)
    elif site not in all_sites:
        # The site must belong to the list defined in the swagger
        return
    else:
        res = meraki.get_devices(site, serial)
    if res is None:
        # Request failed
        return
    aps = []
    for device in res:
        try:
            # Get building and floor from device name
            _site, _AP, building, floor, _index = device['name'].split('-')
        except (ValueError, AttributeError):
            # Default values if device name is correctly formatted
            building = None
            floor = None
        aps.append({
            'name': device['name'],
            'serial': device['serial'],
            'lat': device['lat'],
            'lng': device['lng'],
            'site': site or device['site'],
            'building': building,
            'floor': floor
        })
    return aps


def get_all():
    """
    Get all AP of the organization

    :return: List of dictionaries describing access points
    """
    res = get_aps()
    if res is None:
        return flask.Response('Organization not found', 404)
    return res


def get_by_site(site):
    """
    Get all AP from a site

    :param site: Site name
    :return: List of dictionaries describing access points
    """
    res = get_aps(site)
    if res is None:
        return flask.Response('Site not found', 404)
    return res


def get_by_serial(site, serial):
    """
    Get a specific AP

    :param site: Site name
    :param serial: Serial of the AP
    :return: Dictionary describing the access point
    """
    res = get_aps(site, serial)
    if res is None:
        return flask.Response('AP not found', 404)
    return res[0]


@init_meraki
def convert_data(site, ap):
    """
    Convert AP data dictionary for a Meraki device

    :param site: Site name
    :param ap: Dictionary describing the access point
    :return: Dictionary describing the Meraki device
    """
    res = meraki.get_devices(site, ap['serial'])

    if res and re.match("^[A-Z]{3}-AP-[A-Z]{3}-[A-Za-z0-9]{1,3}-[0-9]{1,3}$", res[0]['name']):
        # Get current index of the existing device if its name is correctly formatted
        _site, _AP, _building, _floor, index = res[0]['name'].split('-')
    else:
        # If the device doesn't exist yet or its name is not correctly formatted, get next available index
        res2 = meraki.get_devices(site)
        pattern = '{}-AP-{}-{}-'.format(site, ap['building'], ap['floor'])
        index_list = [int(dic.get('name', '')[len(pattern):])
                      for dic in res2 if dic['name'] and dic['name'].startswith(pattern)]
        index_list.append(0)
        index = max(index_list) + 1

    # Build the device name according to the pattern SITE-AP-BUILDING-FLOOR-INDEX
    data = {'name': '{}-AP-{}-{}-{}'.format(site, ap['building'], ap['floor'], index)}

    if 'lat' in ap:
        data['lat'] = ap['lat']
    if 'lng' in ap:
        data['lng'] = ap['lng']

    return data


@init_meraki
def create(site, ap):
    """
    Create an AP in a site

    :param site: Site name
    :param ap: Dictionary describing the access point
    :return: Response with status code
    """
    res = meraki.create_device(site, ap['serial'], convert_data(site, ap))
    if res != requests.codes.created:
        return flask.Response('AP creation failed', 403)
    return flask.Response('AP created', 201)


@init_meraki
def update(site, ap):
    """
    Update AP in site

    :param site: Site name
    :param ap: Dictionary describing the access point
    :return: Response with status code
    """
    res = meraki.update_device(site, ap['serial'], convert_data(site, ap))
    if res != requests.codes.ok:
        return flask.Response('AP update failed', 403)
    return flask.Response('AP updated', 200)


@init_meraki
def create_multiple(ap_list):
    """
    Create multiple AP in sites

    :param ap_list: List of dictionaries describing access points
    :return: Response with status code
    """
    for ap in ap_list:
        res = meraki.create_device(ap['site'], ap['serial'], convert_data(ap['site'], ap))
        if res != requests.codes.created:
            return flask.Response('APs creation failed', 403)
    return flask.Response('APs created', 201)


@init_meraki
def remove(site, serial):
    """
    Remove AP from site

    :param site: Site name
    :param serial: Serial of the AP
    :return: Response with status code
    """
    res = meraki.remove_device(site, serial)
    if res != requests.codes.no_content:
        return flask.Response('AP removal failed', 403)
    return flask.Response('AP removed', 200)


if __name__ == '__main__':
    # Connexion app starting
    app = connexion.App(__name__)
    app.add_api('swagger.yaml')
    app.run(host='127.0.0.1', port=8080)
