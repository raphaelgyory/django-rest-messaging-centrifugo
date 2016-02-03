# coding=utf8
# -*- coding: utf8 -*-
# vim: set fileencoding=utf8 :

from __future__ import unicode_literals


def build_channel(namespace, name, user_ids):
    """ Creates complete channel information as described here https://fzambia.gitbooks.io/centrifugal/content/server/channels.html. """
    ids = ','.join(map(str, user_ids))
    return "{0}:{1}#{2}".format(namespace, name, ids)
