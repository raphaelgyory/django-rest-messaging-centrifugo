# coding=utf8
# -*- coding: utf8 -*-
# vim: set fileencoding=utf8 :

from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    """ View handling javascript. """
    return render(request, "tests/index.html")


def dummy(request):
    """ View doing nothing. """
    return HttpResponse('Signin in')
