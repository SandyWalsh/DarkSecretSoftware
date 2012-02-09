from django.shortcuts import render_to_response
import logging
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
    context = {}
    return context


def home(request, state=None):
    if not state:
        state = get_state(request)
    return render_to_response('stackmon/index.html', default_context(state)) 


def foo(request, state=None):
    if not state:
        state = get_state(request)
    return render_to_response('stackmon/foo.html', default_context(state)) 


def query(request):
    state = get_state(request)

    text = request.POST.get('query', "").lower()
    verb, target = parse_command(text)

    response = [(False, "Syntax Error"),]
    if verb in CMDS:
        try:
            response = CMDS[verb](state, 
                                  verb=verb, target_name=target,
                                  cmds=CMDS)
        except GameException, e:
            response = [(False, e.desc), ]
        except StartOver, e:
            state = reset(request)
            response = [(False, "Game reset."), ]
        except Exception, e:
            response = [(False, e), ]
    context = default_context(state)
    state.save(request)
    if response:
        context['text'] = response
        return render_to_response('query.html', context)
    return render_to_response('look.html', context)
