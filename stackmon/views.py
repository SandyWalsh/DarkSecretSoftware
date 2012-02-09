from django.shortcuts import render_to_response
import json
import logging
import pprint
import random
import sys

logger = logging.getLogger(__name__)

VERSION = 1


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
    args = request.POST.get('args', "{}")
    args = json.loads(args)
    c = default_context(state)
    pp = pprint.PrettyPrinter(depth=2)
    c['cooked_args'] = args #pp.pformat(args)
    return render_to_response('stackmon/data.html', c)


def host_status(request):
    state = get_state(request)
    c = default_context(state)
    return render_to_response('stackmon/host_status.html', c)


def instance_status(request):
    state = get_state(request)
    c = default_context(state)
    return render_to_response('stackmon/instance_status.html', c)
