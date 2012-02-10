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
    publisher = body['publisher_id']
    parts = publisher_id.split('.')   
    service = parts[0]
    host = parts[1]
    instance = body['payload'].get('instance_id', None)
    event = body['event_type']
    return dict(host=host, instance=instance, publisher=publisher,
                service=service, event=event)
                

def _compute_update_message(routing_key, body):
    publisher = "n/a"
    args = body['args']
    host = args['host']
    service = args['service_name']
    event = body['method']
    instance = 'n/a'
    return dict(host=host, instance=instance, publisher=publisher,
                service=service, event=event)

# routing_key : handler
HANDLERS = {'monitor.info':_monitor_message,
            'monitor.error':_monitor_message,
            '':_compute_update_message}


def _parse(tenant_id, args, json_args):
    routing_key, body = args
    handler = HANDLERS.get(routing_key, None)
    if handler:
        values = handler(tenant_id, routing_key, body)
        if not values:
            return
        values['when'] = body['_context_timestamp')
        values['publisher'] = body['publisher_id']
        values['when'] = datetime.strptime(when, "%Y-%m-%dT%H:%M:%S.%f")
        values['routing_key'] = routing_key
        record = models.RawData(**values)
        record.save()


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
