# coding=utf8
# -*- coding: utf8 -*-
# vim: set fileencoding=utf8 :

from __future__ import unicode_literals
import sys


PYV = sys.version_info


def compat_json_resp_content(response_content):
    """ Python 3 cannot do json.loads on bytes. """
    if PYV[0] >= 3:
        return response_content.decode()
    else:
        return response_content
