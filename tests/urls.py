# coding=utf8
# -*- coding: utf8 -*-
# vim: set fileencoding=utf8 :

from __future__ import unicode_literals
from django.conf.urls import include, url
from tests.views import dummy, index

urlpatterns = [
    url(r'^messaging/centrifugo/', include('rest_messaging_centrifugo.urls', namespace='rest_messaging_centrifugo')),
]

# we add the testing view
urlpatterns += [
    url(r'^messaging/centrifugo/dummy/', dummy, name='dummy'),
    url(r'^messaging/centrifugo/tests/', index, name='index'),
]
