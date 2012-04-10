# Copyright 2012 - Dark Secret Software Inc.

from django.shortcuts import render_to_response
from django import http
from django import template
from django.utils.functional import wraps

import datetime
import json
import logging
import pprint
import random
import sys

logger = logging.getLogger(__name__)

VERSION = 4


class State(object):
    def __init__(self):
        self.version = VERSION
 
    def __str__(self):
        return "[Version %s]" % (self.version, )
 

def _reset_state(request):
    state = State()
    request.session['state'] = state
    return state

   
def _get_state(request):
    if 'state' in request.session:
        state = request.session['state']
    else:
        state =_reset_state(request)

    if hasattr(state, 'version') and state.version < VERSION:
        state =_reset_state(request)
        
    return state


def _default_context(state):
    context = dict(utc=datetime.datetime.utcnow(), state=state)
    return context

    
def welcome(request):
    state = _reset_state(request)
    return render_to_response('pizza/index.html', _default_context(state))


def order(request):
    state = _reset_state(request)
    return render_to_response('pizza/order.html', _default_context(state))
