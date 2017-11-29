#!/usr/bin/env python
# coding: utf-8
"""
Test ap module
"""

from __future__ import absolute_import

import unittest

import ap
from meraki import Meraki


class TestAp(unittest.TestCase):
    """
    Test base functions
    """

    def setUp(self):
        """
        Initialization of the API and reference objects
        """
        organization = "STELIA-SAS-DEV"
        ap.meraki = Meraki(ap.api_key, ap.api_url, organization)
        self.ap = {
            'name': 'TLS-AP-SKP-1c-1',
            'site': 'TLS',
            'building': 'SKP',
            'floor': '1c',
            'serial': 'Q2KD-23RT-XR3D',
            'lat': 21.0,
            'lng': 33.0
        }
        self.ap_to_create = self.ap.copy()
        self.ap_to_create.pop('name')
        self.ap_to_update = self.ap_to_create.copy()
        self.ap_to_update['building'] = 'PKS'
        self.ap_to_update['floor'] = '2'
        self.ap_to_update['lat'] = 8.54151521651531
        self.ap_to_update['lng'] = 10.6854961253256
        self.ap_updated = self.ap_to_update.copy()
        self.ap_updated['name'] = 'TLS-AP-PKS-2-1'
        self.ap2 = {
            'name': 'TLS-AP-SKP-1c-2',
            'site': 'TLS',
            'building': 'SKP',
            'floor': '1c',
            'serial': 'Q2KD-2F3G-V4LB',
            'lat': 21.0,
            'lng': 33.0
        }
        self.ap2_to_create = self.ap2.copy()
        self.ap2_to_create.pop('name')
        self.ap3 = {
            'name': 'MLT-AP-COL-3a-1',
            'site': 'MLT',
            'building': 'COL',
            'floor': '3a',
            'serial': 'Q2KD-2UM5-CLUF',
            'lat': 5.56461,
            'lng': 42.5465
        }
        self.ap3_to_create = self.ap3.copy()
        self.ap3_to_create.pop('name')

    def test_01_create_ap(self):
        """
        Test creation of an AP
        """
        res = ap.create('TLS', self.ap_to_create)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data, b'AP created')

    def test_04_create_existing_ap(self):
        """
        Test creation failure of an existing AP
        """
        res = ap.create('TLS', self.ap_to_create)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, b'AP creation failed')

    def test_06_create_multiple_ap(self):
        """
        Test creation of multiple AP
        """
        res = ap.create_multiple([self.ap2_to_create, self.ap3_to_create])
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data, b'APs created')

    def test_20_get_by_serial(self):
        """
        Test get an AP by serial
        """
        res = ap.get_by_serial('TLS', 'Q2KD-23RT-XR3D')
        self.assertEqual(res, self.ap)

    def test_30_get_by_site(self):
        """
        Test get all AP from site
        """
        res = ap.get_by_site('TLS')
        res = sorted(res, key=lambda k: k['serial'])
        ref = [self.ap, self.ap2]
        ref = sorted(res, key=lambda k: k['serial'])
        self.assertEqual(res, ref)

    def test_40_update(self):
        """
        Test update of an AP
        """
        res = ap.update('TLS', self.ap_to_update)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, b'AP updated')

    def test_60_get_all(self):
        """
        Test get all AP
        """
        res = ap.get_all()
        res = sorted(res, key=lambda k: k['serial'])
        ref = [self.ap, self.ap2, self.ap3]
        ref = sorted(res, key=lambda k: k['serial'])
        self.assertEqual(res, ref)

    def test_80_remove(self):
        """
        Test remove AP
        """
        res = ap.remove('TLS', 'Q2KD-23RT-XR3D')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, b'AP removed')

        res = ap.remove('TLS', 'Q2KD-2F3G-V4LB')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, b'AP removed')

        res = ap.remove('MLT', 'Q2KD-2UM5-CLUF')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, b'AP removed')

        res = ap.get_by_serial('TLS', 'Q2KD-23RT-XR3D')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data, b'AP not found')

        res = ap.get_by_serial('TLS', 'Q2KD-2F3G-V4LB')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data, b'AP not found')

        res = ap.get_by_serial('MLT', 'Q2KD-2UM5-CLUF')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data, b'AP not found')

        res = ap.get_all()
        self.assertEqual(res, [])

    def test_94_remove_absent_ap(self):
        """
        Test remove absent AP
        """
        res = ap.remove('TLS', 'Q2KD-23RT-XR3D')
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, b'AP removal failed')

    def test_98_update_absent_ap(self):
        """
        Test update absent AP
        """
        res = ap.update('TLS', self.ap_to_update)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, b'AP update failed')


if __name__ == '__main__':
    unittest.main()
