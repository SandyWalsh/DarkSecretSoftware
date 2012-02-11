# Copyright 2012 - Dark Secret Software Inc.

from django.shortcuts import render_to_response

from dss.stackmon import models

import datetime
import json
import logging
import pprint
import random
import sys

logger = logging.getLogger(__name__)

VERSION = 1


def _monitor_message(routing_key, body):
    event = body['event_type']
    publisher = body['publisher_id']
    parts = publisher.split('.')   
    service = parts[0]
    host = parts[1]
    payload = body['payload']
    request_spec = payload.get('request_spec', None)
    instance = None
    instance = payload.get('instance_id', instance)
    nova_tenant = body.get('_context_project_id', None)
    nova_tenant = payload.get('tenant_id', nova_tenant)
    return dict(host=host, instance=instance, publisher=publisher,
                service=service, event=event, nova_tenant=nova_tenant)
                

def _compute_update_message(routing_key, body):
    publisher = "n/a"
    args = body['args']
    host = args['host']
    service = args['service_name']
    event = body['method']
    instance = 'n/a'
    nova_tenant = args.get('_context_project_id', None)
    return dict(host=host, instance=instance, publisher=publisher,
                service=service, event=event, nova_tenant=nova_tenant)


# routing_key : handler
HANDLERS = {'monitor.info':_monitor_message,
            'monitor.error':_monitor_message,
            '':_compute_update_message}


def _parse(tenant, args, json_args):
    routing_key, body = args
    handler = HANDLERS.get(routing_key, None)
    if handler:
        values = handler(routing_key, body)
        if not values:
            return {}

        values['tenant'] = tenant
        when = body['_context_timestamp']
        when = datetime.datetime.strptime(when, "%Y-%m-%dT%H:%M:%S.%f")
        values['when'] = when
        values['microseconds'] = when.microsecond
        values['routing_key'] = routing_key
        values['json'] = json_args
        record = models.RawData(**values)
        record.save()
        return values
    return {}


def _post_process_raw_data(rows):
    for row in rows:
        if "error" in row.routing_key:
            row.is_error = True


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
    context = dict(utc=datetime.datetime.utcnow())
    return context


def home(request):
    state = get_state(request)
    return render_to_response('stackmon/index.html', default_context(state)) 


def data(request):
    state = get_state(request)
    raw_args = request.POST.get('args', "{}")
    args = json.loads(raw_args)
    c = default_context(state)
    fields = _parse(0, args, raw_args)
    c['cooked_args'] = fields
    return render_to_response('stackmon/data.html', c)


def details(request, column, row_id):
    state = get_state(request)
    c = default_context(state)
    row = models.RawData.objects.get(pk=row_id)
    value = getattr(row, column)
    rows = models.RawData.objects.filter(**{column:value}).\
                                  order_by('-when', '-microseconds')[:200]
    _post_process_raw_data(rows)
    c['rows'] = rows
    c['allow_expansion'] = True
    return render_to_response('stackmon/rows.html', c)


def expand(request, row_id):
    state = get_state(request)
    c = default_context(state)
    row = models.RawData.objects.get(pk=row_id)
    payload = json.loads(row.json)
    pp = pprint.PrettyPrinter()
    c['payload'] = pp.pformat(payload)
    return render_to_response('stackmon/expand.html', c)


def host_status(request):
    state = get_state(request)
    c = default_context(state)
    hosts = models.RawData.objects.filter(host__gt='').order_by('-when', '-microseconds')[:20]
    _post_process_raw_data(hosts)
    c['rows'] = hosts
    return render_to_response('stackmon/host_status.html', c)


def instance_status(request):
    state = get_state(request)
    c = default_context(state)
    instances = models.RawData.objects.exclude(instance='n/a').exclude(instance__isnull=True).order_by('-when', '-microseconds')[:20]
    _post_process_raw_data(instances)
    c['rows'] = instances
    return render_to_response('stackmon/instance_status.html', c)
