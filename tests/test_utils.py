# coding=utf8
# -*- coding: utf8 -*-
# vim: set fileencoding=utf8 :

from __future__ import unicode_literals

from django.test import TestCase
from rest_messaging_centrifugo.utils import build_channel


class TestUtils(TestCase):

    def test_build_channel(self):
        namespace = "message"
        name = 1
        ids = [1, 2, 3]
        built = build_channel(namespace=namespace, name=name, user_ids=ids)
        self.assertEqual(built, "message:1#1,2,3".format(namespace, name, ids))
