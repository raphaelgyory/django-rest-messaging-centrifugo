# coding=utf8
# -*- coding: utf8 -*-
# vim: set fileencoding=utf8 :

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.staticfiles.testing import LiveServerTestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from selenium.webdriver.firefox.webdriver import WebDriver

from rest_messaging.models import Message, Participant, Participation, Thread
from rest_messaging_centrifugo.utils import build_channel

from cent.core import Client

# sudo apt-get install xvfb
# sudo apt-get install xserver-xephyr
# sudo apt-get install tightvncserver
# pip install pyvirtualdisplay
from pyvirtualdisplay import Display

import os
import signal
import subprocess
import time


@override_settings(CENTRIFUGO_PORT=8802, CENTRIFUGE_ADDRESS='http://localhost:{0}/'.format(8802))
class IntegrationTests(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(IntegrationTests, cls).setUpClass()
        # we do not display
        cls.display = Display(visible=0, size=(1024, 768))
        cls.display.start()
        cls.selenium = WebDriver()
        # we create a user
        password = "password"
        cls.user = User(username="UserForLiveTests")
        cls.user.set_password(password)
        cls.user.save()
        # we log him in
        # source http://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        # we need a session
        session = SessionStore()
        session[SESSION_KEY] = cls.user.id
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[HASH_SESSION_KEY] = cls.user.get_session_auth_hash()
        session.save()
        # the cookie dict
        cls.cookie = {
            'name': settings.SESSION_COOKIE_NAME,
            'value': session.session_key,
            'secure': False,
            'path': '/',
        }
        # we launch centrifugo
        cls.centrifugo = subprocess.Popen(["centrifugo --config=tests/config.json --port={0}".format(getattr(settings, "CENTRIFUGO_PORT", 8802))], stdout=subprocess.PIPE,
                                          shell=True, preexec_fn=os.setsid)
        # we create a thread
        cls.participant1 = Participant.objects.create(id=cls.user.id)
        cls.participant2 = Participant.objects.create(id=2)
        cls.participant3 = Participant.objects.create(id=3)
        # we create threads
        cls.thread1 = Thread.objects.create(name="The #1 Thread")
        cls.participation11 = Participation.objects.create(participant=cls.participant1, thread=cls.thread1)
        cls.participation12 = Participation.objects.create(participant=cls.participant2, thread=cls.thread1)
        cls.thread2 = Thread.objects.create(name="The #2 Thread")
        cls.participation21 = Participation.objects.create(participant=cls.participant1, thread=cls.thread2)
        cls.participation22 = Participation.objects.create(participant=cls.participant3, thread=cls.thread2)
        cls.thread_unrelated = Thread.objects.create(name="The unrelated Thread")  # the conversation does not involve the current user, we do not want it on the screen!
        cls.participationU1 = Participation.objects.create(participant=cls.participant2, thread=cls.thread_unrelated)
        cls.participationU2 = Participation.objects.create(participant=cls.participant3, thread=cls.thread_unrelated)
        # and wait for it to run
        time.sleep(4)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.close()
        cls.selenium.quit()
        cls.display.stop()
        # we stop centrifugo
        # sudo kill `sudo lsof -t -i:xxxx`
        os.killpg(cls.centrifugo.pid, signal.SIGTERM)
        super(IntegrationTests, cls).tearDownClass()

    def test_integration(self):
        # we hit whatever view just to set the cookie
        self.selenium.get(self.live_server_url + reverse('dummy'))
        self.selenium.add_cookie(self.cookie)
        self.selenium.refresh()
        # we load the index page which contains the logic (in javascript)
        self.selenium.get(self.live_server_url + reverse('index'))
        # we wait a little bit
        time.sleep(4)
        # we create a message
        # this will trigger a publishing signal in django-rest-messaging-centrifugo
        body11 = "hi #11"
        body12 = "hi #12"
        body21 = "hi #21"
        body22 = "hi #22"
        bodyU1 = "We do not want to see this! #1"
        bodyU2 = "We do not want to see this! #2"
        m11 = Message.objects.create(sender=self.participant1, thread=self.thread1, body=body11)
        m12 = Message.objects.create(sender=self.participant2, thread=self.thread1, body=body12)
        m21 = Message.objects.create(sender=self.participant3, thread=self.thread2, body=body21)
        m22 = Message.objects.create(sender=self.participant1, thread=self.thread2, body=body22)
        mU1 = Message.objects.create(sender=self.participant2, thread=self.thread_unrelated, body=bodyU1)
        mU2 = Message.objects.create(sender=self.participant3, thread=self.thread_unrelated, body=bodyU2)
        self.participation11.save()  # to trigger the signal
        # the channels are private
        # this means that Centrifugo will check the users ids to know if the user may connect
        # if we query a private channel the user does not belong to, we never see the message
        client = Client("{0}api/".format(getattr(settings, "CENTRIFUGE_ADDRESS")), getattr(settings, "CENTRIFUGE_SECRET"))
        forbidden_message = "Message forbidden"
        client.publish(
            build_channel(namespace=settings.CENTRIFUGO_MESSAGE_NAMESPACE, name=self.thread_unrelated.id, user_ids=[p.id for p in self.thread_unrelated.participants.all()]),
            forbidden_message
        )
        # we wait a little bit
        time.sleep(4)
        # now the messages should be displayed
        m11 = self.selenium.find_element_by_id('message__{0}'.format(m11.id))
        m12 = self.selenium.find_element_by_id('message__{0}'.format(m12.id))
        m21 = self.selenium.find_element_by_id('message__{0}'.format(m21.id))
        m22 = self.selenium.find_element_by_id('message__{0}'.format(m22.id))
        self.assertTrue(body11 in m11.text)
        self.assertTrue(body12 in m12.text)
        self.assertTrue(body21 in m21.text)
        self.assertTrue(body22 in m22.text)
        # and the list of connected threads too
        message_channel_to_connect_to = 'messages:{0}#{1},{2}'.format(self.participation11.thread.id, self.participation11.thread.participants.all()[0].id, self.participation11.thread.participants.all()[1].id)
        thread_messages = self.selenium.find_element_by_id('thread__{0}'.format(message_channel_to_connect_to))
        self.assertTrue(message_channel_to_connect_to in thread_messages.text)
        self.assertRaises(Exception, self.selenium.find_element_by_id, 'message__{0}'.format(mU1.id))
        self.assertRaises(Exception, self.selenium.find_element_by_id, 'message__{0}'.format(mU2.id))
        self.assertRaises(Exception, self.selenium.find_element_by_id, 'message__{0}'.format(mU2.id))
        self.assertEqual([], self.selenium.find_elements_by_xpath("//*[contains(text(), '{0}')]".format(forbidden_message)))
