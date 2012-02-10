# Copyright 2012 - Dark Secret Software Inc.

from django.shortcuts import render_to_response

from stackmon import models

import datetime
import json
import logging
import pprint
import random
import sys

logger = logging.getLogger(__name__)

VERSION = 1


def _monitor_message(routing_key, body):
    publisher_id = body['publisher_id']
    parts = publisher_id.split('.')   
    host = parts[1]
    instance = body['payload'].get('instance_id', None)
    return (host, instance)

def _compute_update_message(routing_key, body):
    host = 
    instance = 
    return (host, instance)


HANDLERS = {'monitor.info':_monitor_message,
            'monitor.error':_monitor_message,
            '':_compute_update_message}

class State(object):
    def __init__(self):
        self.version = VERSION


def get_state(request):
    if 'state' in request.session:
        state = request.session['state']
        if hasattr(state, 'version') and state.version >= VERSION:
            return state

    state = State()
    request.session['state'] = state
    return state


def default_context(state):
    context = dict(number=random.randrange(1000))
    return context


def home(request):
    state = get_state(request)
    return render_to_response('stackmon/index.html', default_context(state)) 


def _parse(tenant_id, args, json_args):
    routing_key, body = args
    handler = HANDLERS.get(routing_key, None)
    if handler:
        host, instance = handler(tenant_id, routing_key, body)
        when = body['_context_timestamp')
        publisher_id = body['publisher_id']
        datetime_when = datetime.strptime(when, "%Y-%m-%dT%H:%M:%S.%f")
        record = models.RawData(host=host, instance=instance, 
                                tenant=tenant_id, json=json_args,
                                publisher=publisher_id,
                                routing_key=routing_key, when=datetime_when)

        record.save()


def data(request):
    state = get_state(request)
    raw_args = request.POST.get('args', "{}")
    args = json.loads(raw_args)
    c = default_context(state)
    pp = pprint.PrettyPrinter(depth=2)
    c['cooked_args'] = args #pp.pformat(args)
    _parse(0, args, raw_args)
    return render_to_response('stackmon/data.html', c)


def host_status(request):
    state = get_state(request)
    c = default_context(state)
    return render_to_response('stackmon/host_status.html', c)


def instance_status(request):
    state = get_state(request)
    c = default_context(state)
    return render_to_response('stackmon/instance_status.html', c)
