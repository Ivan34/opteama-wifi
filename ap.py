#!/usr/bin/env python3
import os

import connexion
import flask

from meraki import Meraki

meraki = None


def get_all():
    return meraki.get_device()


def post_bulk(ap_list):
    pass


def get_by_site(site):
    return meraki.get_device(site)


def post_by_site(site, ap):
    res = meraki.post_device(
        ap['serial'],
        ap['site'],
        ap['building'],
        ap['floor'],
        ap.get('lat'),
        ap.get('lon')
    )
    if not res:
        return flask.Response('AP deployment failed', 400)
    return flask.Response('AP deployed', 200)


def put_by_site(site, ap):
    res = meraki.update_device(
        ap['serial'],
        ap['site'],
        ap.get('building'),
        ap.get('floor'),
        ap.get('lat'),
        ap.get('lon')
    )
    if not res:
        return flask.Response('AP update failed', 400)
    return flask.Response('AP updated', 200)


def delete_by_site(site, ap):
    res = meraki.remove_device(site, ap['serial'])
    if not res:
        return flask.Response('AP undeployment failed', 400)
    return flask.Response('AP undeployed', 200)


if __name__ == '__main__':
    # Meraki parameters
    api_url = "https://api.meraki.com/api/v0/"
    api_key = os.getenv("MERAKI_API_KEY")
    if not api_key:
        raise Exception("Meraki API key missing")
    organization = "STELIA-SAS-PROD"
    meraki = Meraki(api_key, api_url, organization)

    # Connexion
    app = connexion.App(__name__)
    app.add_api('swagger.yaml')
    app.run(host='127.0.0.1', port=8080)
