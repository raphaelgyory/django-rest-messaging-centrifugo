# coding=utf8
# -*- coding: utf8 -*-
# vim: set fileencoding=utf8 :

from __future__ import unicode_literals

from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from cent.core import generate_token
from rest_messaging.models import Participant, Thread
from rest_messaging_centrifugo.utils import build_channel

import json
import time


class CentrifugoAuthentication(View):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CentrifugoAuthentication, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Returns a token identifying the user in Centrifugo.
        """

        current_timestamp = "%.0f" % time.time()
        user_id_str = u"{0}".format(request.user.id)
        token = generate_token(settings.CENTRIFUGE_SECRET, user_id_str, "{0}".format(current_timestamp), info="")

        # we get all the channels to which the user can subscribe
        participant = Participant.objects.get(id=request.user.id)

        # we use the threads as channels ids
        channels = []
        for thread in Thread.managers.get_threads_where_participant_is_active(participant_id=participant.id):
            channels.append(
                # "{0}{1}".format(settings.CENTRIFUGO_MESSAGE_NAMESPACE, thread.id)
                build_channel(settings.CENTRIFUGO_MESSAGE_NAMESPACE, thread.id, thread.participants.all())
            )

        # we also have a channel to alert us about new threads
        threads_channel = build_channel(settings.CENTRIFUGO_THREAD_NAMESPACE, request.user.id, [request.user.id])  # he is the only one to have access to the channel
        channels.append(threads_channel)

        # we return the information
        to_return = {
            'user': user_id_str,
            'timestamp': current_timestamp,
            'token': token,
            'connection_url': "{0}connection/".format(settings.CENTRIFUGE_ADDRESS),
            'channels': channels,
            'debug': settings.DEBUG,
        }

        return HttpResponse(json.dumps(to_return), content_type='application/json; charset=utf-8')

# NOT USED
# We use user channel boundary (https://fzambia.gitbooks.io/centrifugal/content/server/channels.html) to filter on users ids
# class CentrifugeChannelAuthorization(View):
#
#   @method_decorator(csrf_exempt)
#   def dispatch(self, request, *args, **kwargs):
#         return super(CentrifugeChannelAuthorization, self).dispatch(request, *args, **kwargs)
#
#   def post(self, request, *args, **kwargs):
#     """
#     Return a hardcoded response.
#     """
#
#     data = ast.literal_eval(request.body)
#     client = data.get("client", "")
#     channels = data.get("channels", [])
#
#     # https://github.com/centrifugal/centrifuge-ruby for example
#
#     # we get the list of the accessible threads
#     #accessible_threads_ids = [thread.id for thread in Thread.managers.get_threads_where_participant_is_active(participant_id=participant.id)]
#
#     to_return = {}
#
#     for channel in channels:
#
#         # we ensure the user has access to this channel's thread
#         thread_id = channel.split(":")[1]
#
#         info = json.dumps({
#                 'channel_extra_info_example': 'you can add additional JSON data when authorizing'
#             })
#         sign = generate_channel_sign(
#             settings.CENTRIFUGE_SECRET, client, channel, info=info
#         )
#         to_return[channel] = {
#             "sign": sign,
#             "info": info,
#         }
#
#
#     return HttpResponse(json.dumps(to_return), content_type='application/json; charset=utf-8')
