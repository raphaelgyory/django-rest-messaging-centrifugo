# coding=utf8
# -*- coding: utf8 -*-
# vim: set fileencoding=utf8 :

from __future__ import unicode_literals

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_messaging.models import Message, Participation
from rest_messaging_centrifugo.utils import build_channel
from cent.core import Client


@receiver([post_save], sender=Message)
def publish_message_to_centrifugo(sender, instance, created, **kwargs):
    """ Publishes each saved message to Centrifugo. """
    if created is True:
        client = Client("{0}api/".format(getattr(settings, "CENTRIFUGE_ADDRESS")), getattr(settings, "CENTRIFUGE_SECRET"))
        client.publish(
            build_channel(settings.CENTRIFUGO_MESSAGE_NAMESPACE, instance.thread.id, [p.id for p in instance.thread.participants.all()]),
            {
                "id": instance.id,
                "body": instance.body,
                "sender": instance.sender.id,
                "thread": instance.thread.id,
                "sent_at": str(instance.sent_at),
            }
        )


# http://stackoverflow.com/questions/11686193/a-signal-m2m-changed-and-bug-with-post-remove
@receiver([post_save], sender=Participation)
def publish_participation_to_thread(sender, instance, created, **kwargs):
    """ Warns users everytime a thread including them is published. This is done via channel subscription.  """
    client = Client("{0}api/".format(getattr(settings, "CENTRIFUGE_ADDRESS")), getattr(settings, "CENTRIFUGE_SECRET"))
    participants = instance.thread.participants.all()
    client.publish(
        build_channel(settings.CENTRIFUGO_THREAD_NAMESPACE, instance.participant.id, [instance.participant.id]),
        {
            "message_channel_to_connect_to": build_channel(settings.CENTRIFUGO_MESSAGE_NAMESPACE, instance.thread.id, [p.id for p in participants])
        }
    )
