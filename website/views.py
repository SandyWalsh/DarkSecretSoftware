from django.shortcuts import render_to_response
import logging
import sys

logger = logging.getLogger(__name__)


VERSION = 1


class State(object):
    def __init__(self):
        self.rooms = ROOMS
        self.room_name = 'road'
        self.backpack = {}
        self.version = VERSION

    def save(self, request):
        request.session['state'] = self

    def get_room(self):
        return self.rooms[self.room_name]


class Item(object):
    def __str__(self):
        return self.name().capitalize()


class Sign(Item):
    def name(self):
        return "sign"

    def verb_read(self):
        return """Dark Secret Software Inc. Corporate Office"""


class Door(Item):
    def __init__(self):
        self.closed = True

    def name(self):
        return "door"

    def verb_open(self):
        if not self.closed:
            return "The door is already open"

        self.closed = False
        return "The door opens effortlessly."

    def verb_close(self):
        if self.closed:
            return "The door is already closed"

        self.closed = True
        return "The door slowly closes and clicks shut."

    def verb_look(self):
        state = ["open", "closed"][self.closed]
        return "A large metal door, painted in a nice neutral color. " \
               "The door is currently %(state)s" % locals()


class GameException(Exception):
    pass


class StartOver(Exception):
    pass


class NoSuchItem(GameException):
    desc = "I don't see that item here" 


class CantDoThat(GameException):
    desc = "I don't know how to do that."


ROOMS = {
    'road' : {
        'short': 'Outside a lovely home.',
        'long': 'You are standing outside a lovely home in rural Nova Scotia, Canada',
        'items': [Sign(), ],
        'exits': ['porch', None, None, None]
    },
    'porch' : {
        'short': 'The front step',
        'long': 'You are on the front step of the house.',
        'items': [Door(), ],
        'exits': [None, None, None, 'road']
    }
}


def get_description(room):
    return room['long']


def reset(request, **kwargs):
    state = State()
    request.session['state'] = state
    return state


def get_state(request):
    if 'state' in request.session:
        state = request.session['state']
        if hasattr(state, 'version') and state.version >= VERSION:
            return state

    return reset(request)


def get_all_items(state):
    items = state.get_room()['items'][:]
    items.extend(state.backpack.keys())
    return items


def get_adjacent_rooms(state):
    room = state.get_room()
    exits = room.get('exits', [None, None, None, None])
    names = ['north', 'east', 'west', 'south']
    zipped = zip(names, exits)
    available_exits = [(dir_name, room_name, state.rooms[room_name])
              for dir_name, room_name in zipped if room_name]
    return available_exits


def default_context(state):
    room = state.get_room()
    items = [str(item) for item in room['items']]

    context = { 'description' : get_description(room),
                'exits' : get_adjacent_rooms(state),
                'items': ', '.join(items),
                'num_items': len(items)}
    return context


def home(request, state=None):
    if not state:
        state = get_state(request)
    return render_to_response('index.html', default_context(state)) 


def start_over(request):
    state = reset(request)
    return home(request, state=state)


def do_reset(state, **kwargs):
    raise StartOver()


def help(state, cmds=[], **kwargs):
    return [(False, "Commands: %s" % ', '.join(cmds.keys())),]


def get_target(state, target_name):
    items = get_all_items(state)
    for item in items:
        if target_name == item.name():
            return item
    raise NoSuchItem()


def check_verb(item, verb_name):
    if hasattr(item, 'verb_%s' % (verb_name, )):
        return item
    raise CantDoThat()
 

def read_item(state, target_name=None, **kwargs):
    target = get_target(state, target_name)
    check_verb(target, "read")
    return [(False, "%s says '%s'" % (target.name(), target.verb_read())), ]


def move(state, verb=None, target_name=None, **kwargs):
    cmd = verb[0]
    room = state.get_room()
    exits = room.get('exits', None)
    if not exits:
        return [(False, "I can't go there."), ]

    if cmd=='g':
        adjacent_rooms = get_adjacent_rooms(state)
        for direction, room_name, room in adjacent_rooms:
            if room_name == target_name:
                state.room_name = target_name
                return None

        return [(False, "I don't know where that is"), ]

    directions = ['n', 'e', 'w', 's']
    direction_index = directions.index(cmd)

    if not exits[direction_index]:
        return [(False, "I don't see any exit in that direction."), ]
        
    state.room_name = exits[direction_index]
    return None


def look(state, target_name=None, **kwargs):
    if not target_name:
        return None

    target = get_target(state, target_name)
    check_verb(target, 'look')
    return [(False, target.verb_look()),]


def do_open(state, target_name=None, **kwargs):
    target = get_target(state, target_name)
    check_verb(target, "open")
    return [(False, target.verb_open()),]


def do_close(state, target_name=None, **kwargs):
    target = get_target(state, target_name)
    check_verb(target, "close")
    return [(False, target.verb_close()),]


CMDS = {
    'help': help,
    '?': help,
    'read': read_item,
    'north': move,
    'south': move,
    'west': move,
    'east': move,
    'go': move,
    'n': move,
    's': move,
    'w': move,
    'e': move,
    'look': look,
    'open': do_open,
    'close': do_close,
    'reset': do_reset,
}


def parse_command(text):
    words = text.split(' ')
    while len(words) < 2:
        words.append(None)
    return tuple(words[:2])


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
