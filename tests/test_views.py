# coding=utf8
# -*- coding: utf8 -*-
# vim: set fileencoding=utf8 :

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, Client as django_client
from rest_messaging.models import Participant, Participation, Thread
from rest_messaging_centrifugo.compat import compat_json_resp_content
from rest_messaging_centrifugo.utils import build_channel
import json


class TestScenario(TestCase):

    def setUp(self):
        # we create a user
        password = "password"
        self.user = User(username="User")
        self.user.set_password(password)
        self.user.save()
        self.client_authenticated = django_client()
        self.client_authenticated.login(username=self.user.username, password=password)
        self.client_unauthenticated = django_client()
        # we create participants and threads
        self.participant1 = Participant.objects.create(id=self.user.id)
        self.participant2 = Participant.objects.create(id=self.user.id + 1)
        self.participant3 = Participant.objects.create(id=self.user.id + 2)
        # we create a thread where all users are in
        self.thread1 = Thread.objects.create(name="Thead 1")
        self.participation1 = Participation.objects.create(participant=self.participant1, thread=self.thread1)
        self.participation2 = Participation.objects.create(participant=self.participant2, thread=self.thread1)
        self.thread2 = Thread.objects.create(name="Thead 2")
        self.participation3 = Participation.objects.create(participant=self.participant1, thread=self.thread2)
        self.participation4 = Participation.objects.create(participant=self.participant3, thread=self.thread2)


class CentrifugoAuthenticationTests(TestScenario):

    def test_token(self):
        # an unauthenticated client will get no token
        response = self.client_unauthenticated.post(reverse('rest_messaging_centrifugo:authentication'), data={})
        self.assertEqual(302, response.status_code)
        # an authenticated client will get a token
        response = self.client_authenticated.post(reverse('rest_messaging_centrifugo:authentication'), data={})
        self.assertEqual(200, response.status_code)
        content = json.loads(compat_json_resp_content(response.content))
        self.assertEqual(int(content["user"]), self.user.id)
        self.assertTrue(content["timestamp"])
        self.assertTrue(content["token"])
        channels = [build_channel(settings.CENTRIFUGO_MESSAGE_NAMESPACE, thread.id, thread.participants.all()) for thread in [self.thread1, self.thread2]] +\
            [build_channel(settings.CENTRIFUGO_THREAD_NAMESPACE, self.user.id, [self.user.id])]
        self.assertEqual(set(content["channels"]), set(channels))
        # get method does not work
        response = self.client_authenticated.get(reverse('rest_messaging_centrifugo:authentication'))
        self.assertEqual(405, response.status_code)
