from django.shortcuts import render_to_response
import logging
import sys

logger = logging.getLogger(__name__)


class Inventory(object):
    def __init__(self):
        self.pack = {}


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

        self.closed = True

    def verb_close(self):
        if not self.closed:
            return "The door is already closed"

        self.closed = False

    def verb_look(self):
        state = ["open", "closed"][self.closed]
        return "A large metal door, painted in a nice neutral color. " \
               "The door is currently %(state)s" % locals()


class GameException(Exception):
    pass


class NoSuchItem(GameException):
    desc = "I don't see that item here" 


class CantDoThat(GameException):
    desc = "I don't know how to do that."


ROOMS = {
    'sign' : {
        'short': 'Outside a lovely home.',
        'long': 'You are standing outside a lovely home in rural Nova Scotia, Canada',
        'items': [Sign(), ],
        'exits': ['porch', None, None, None]
    },
    'porch' : {
        'short': 'The front step',
        'long': 'You are on the front step of the house.',
        'items': [Door(), ],
        'exits': [None, None, None, 'sign']
    }
}


def get_description(room):
    return room['long']


def get_current_room(request):
    room_name = request.session.get('room', 'sign')
    return ROOMS[room_name]


def move_to(request, room_name):
    request.session['room'] = room_name


def get_inventory(request):
    return request.session.get('backpack', [])


def get_all_items(request, room):
    items = room['items']
    items.extend(get_inventory(request))
    return items


def default_context(request):
    room = get_current_room(request)
    items = [str(item) for item in room['items']]
    context = { 'description' : get_description(room),
                'items': ', '.join(items),
                'num_items': len(items)}
    return context


def home(request):
    return render_to_response('index.html', default_context(request)) 


def help(request, cmds=[], **kwargs):
    return [(False, "Commands: %s" % ', '.join(cmds.keys())),]


def get_target(request, target_name):
    room = get_current_room(request)
    items = get_all_items(request, room)
    for item in items:
        if target_name == item.name():
            return item
    raise NoSuchItem()


def check_verb(item, verb_name):
    if hasattr(item, 'verb_%s' % (verb_name, )):
        return item
    raise CantDoThat()
 

def read_item(request, target_name=None, **kwargs):
    target = get_target(request, target_name)
    check_verb(target, "read")
    return [(False, "%s says '%s'" % (target.name(), target.verb_read())), ]


def move(request, verb=None, target_name=None, **kwargs):
    cmd = verb[0]
    room = get_current_room(request)
    exits = room.get('exits', None)
    if not exits:
        return "I can't go there."

    if cmd=='g':
        target = get_target(request, target_name)
        move_to(target.name)
        return None

    directions = ['n', 'e', 'w', 's']
    direction_index = directions.index(cmd)

    if not exits[direction_index]:
        return "I don't see any exit in that direction."
        
    move_to(request, exits[direction_index])
    return None


def look(request, target_name=None, **kwargs):
    if not target_name:
        return None

    target = get_target(request, target_name)
    check_verb(target, 'look')
    return [(False, target.verb_look()),]


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
}


def parse_command(text):
    words = text.split(' ')
    while len(words) < 2:
        words.append(None)
    return tuple(words[:2])


def query(request):
    text = request.POST.get('query', "").lower()
    verb, target = parse_command(text)
    response = [(False, "Syntax Error"),]
    if verb in CMDS:
        try:
            response = CMDS[verb](request,
                                  verb=verb, target_name=target,
                                  cmds=CMDS)
        except GameException, e:
            response = [(False, e.desc), ]
        except Exception, e:
            response = [(False, e), ]
    context = default_context(request)
    if response:
        context['text'] = response
        return render_to_response('query.html', context)
    return render_to_response('look.html', context)
