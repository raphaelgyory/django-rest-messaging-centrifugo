# coding=utf8
# -*- coding: utf8 -*-
# vim: set fileencoding=utf8 :

from __future__ import unicode_literals
from django.conf.urls import url
from rest_messaging_centrifugo import views

urlpatterns = [
    url(r'^authentication/$', views.CentrifugoAuthentication.as_view(), name='authentication'),
]
