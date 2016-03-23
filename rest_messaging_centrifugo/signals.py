# coding=utf8
# -*- coding: utf8 -*-
# vim: set fileencoding=utf8 :

from __future__ import unicode_literals

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_messaging.models import Message, Participation, Thread
from rest_messaging_centrifugo.utils import build_channel
from cent.core import Client


@receiver([post_save], sender=Message)
def publish_message_to_centrifugo(sender, instance, created, **kwargs):
    """ Publishes each saved message to Centrifugo. """
    if created is True:
        client = Client("{0}api/".format(getattr(settings, "CENTRIFUGE_ADDRESS")), getattr(settings, "CENTRIFUGE_SECRET"))
        # we ensure the client is still in the thread (he may have left or have been removed)
        active_participants = [participation.participant.id for participation in Participation.objects.filter(thread=instance.thread, date_left__isnull=True).select_related('participant')]
        client.publish(
            build_channel(settings.CENTRIFUGO_MESSAGE_NAMESPACE, instance.thread.id, active_participants),
            {
                "id": instance.id,
                "body": instance.body,
                "sender": instance.sender.id,
                "thread": instance.thread.id,
                "sent_at": str(instance.sent_at),
                "is_notification": True,  # ATTENTION: check against sender too to be sure to not notify him his message
            }
        )


# http://stackoverflow.com/questions/11686193/a-signal-m2m-changed-and-bug-with-post-remove
@receiver([post_save], sender=Thread)
def publish_participation_to_thread(sender, instance, created, **kwargs):
    """ Warns users everytime a thread including them is published. This is done via channel subscription.  """
    if kwargs.get('created_and_add_participants') is True:
        request_participant_id = kwargs.get('request_participant_id')
        if request_participant_id is not None:
            client = Client("{0}api/".format(getattr(settings, "CENTRIFUGE_ADDRESS")), getattr(settings, "CENTRIFUGE_SECRET"))
            active_participants = [participation.participant for participation in Participation.objects.filter(thread=instance, date_left__isnull=True).select_related('participant')]
            for participant in active_participants:
                client.publish(
                    build_channel(settings.CENTRIFUGO_THREAD_NAMESPACE, participant.id, [participant.id]),
                    {
                        "message_channel_to_connect_to": build_channel(settings.CENTRIFUGO_MESSAGE_NAMESPACE, instance.id, [p.id for p in active_participants])
                    }
                )
