from django.shortcuts import render_to_response
import logging
import sys

logger = logging.getLogger(__name__)


VERSION = 7


class GameException(Exception):
    pass


class StartOver(Exception):
    pass


class NoSuchItem(GameException):
    desc = "I don't see that item here" 


class NotInBackpack(GameException):
    desc = "You don't have that item in your backpack."


class CantDoThat(GameException):
    desc = "I don't know how to do that."


class State(object):
    def __init__(self):
        self.rooms = ROOMS
        self.room_name = 'road'
        self.backpack = []
        self.version = VERSION

    def save(self, request):
        request.session['state'] = self

    def get_room(self, room_name = None):
        if not room_name:
            room_name = self.room_name
        return self.rooms[room_name]

    def get_item(self, item_name):
        items = self.get_all_items()
        for item in items:
            if item.name() == item_name:
                return item
        raise NoSuchItem()

    def remove_item(self, room, item):
        items = room['items']
        index = items.index(item)
        del items[index]
        
    def add_item(self, room, item):
        room['items'].append(item)

    def add_to_backpack(self, item):
        item.is_in_backpack = True
        self.backpack.append(item)

    def remove_from_backpack(self, item):
        index = self.backpack.index(item)
        del self.backpack[index]
        item.is_in_backpack = False

    def get_target_from_backpack(self, item_name):
        for item in self.backpack:
            if item.name() == item_name:
                return item
        raise NotInBackpack()

    def get_target(self, target_name):
        items = self.get_all_items()
        for item in items:
            if target_name == item.name():
                return item
        raise NoSuchItem()

    def get_all_items(self):
        items = self.get_room()['items'][:]
        items.extend(self.backpack)
        return items


class Item(object):
    def __init__(self, can_take=False):
        self.is_in_backpack = False
        self.can_take = can_take

    def __str__(self):
        return self.name().capitalize()

    def verb_take(self, state):
        return self.can_take and not self.is_in_backpack


class TakeableItem(Item):
    def __init__(self):
        super(TakeableItem, self).__init__(can_take=True)


class Sign(Item):
    def name(self):
        return "sign"

    def verb_read(self):
        return "Dark Secret Software Inc. Corporate Office. Go inside for contact information."


class Axe(TakeableItem):
    def name(self):
        return "axe"

    def verb_look(self):
        return """A sharp splitting axe."""

    def verb_use(self, state):
        if not state.room_name == "porch":
            return "You check the axe with your fingernail. It's very sharp."

        room = state.get_room()
        door = state.get_item("door")
        if door.locked:
            door.locked = False
            return "You smash the lock on the door. It shatters."
        else:
            return "Don't you think you've done enough already?"


class Trampoline(Item):
    def name(self):
        return "trampoline"

    def verb_look(self):
        return "A large oval trampoline surrounded by a large net."

    def verb_use(self, state):
        return "Wee! You bounce up and down on the trampoline. It's fun."


class ZiplineTether(Item):
    def name(self):
        return "tether"

    def verb_look(self):
        return "A sturdy rope attached to a pulley on the zipline."

    def verb_use(self, state):
        last_room_name = state.room_name
        if state.room_name == 'trampoline':
            state.room_name = 'garden'
        elif state.room_name == 'garden':
            state.room_name = 'trampoline'

        last_room = state.get_room(last_room_name)
        state.remove_item(last_room, self)
        room = state.get_room()
        state.add_item(room, self)
        return "You sail along the zipline to the other side of the yard, avoiding the mud."


class Key(TakeableItem):
    def name(self):
        return "key"
        
    def verb_look(self):
        return """The key has a USB connector and 'DSS' engraved on the side."""

    def verb_use(self, state):
        if not state.room_name == "foyer":
            return "There's nowhere to plug it in."

        room = state.get_room()
        computer = state.get_item("computer")
        if computer.locked:
            computer.locked = False
            return "You slide the key into the USB slot of the PC. The PC springs to life."
        else:
            return "Nothing happens."


class Computer(Item):
    def __init__(self):
        self.locked = True
        super(Computer, self).__init__()

    def name(self):
        return "computer"

    def verb_look(self):
        status = ""
        if self.locked:
            status = "The computer appears to be locked."
        return "A desktop computer which seems to be running Ubuntu. It has a USB port on the front. %s" % status

    def verb_use(self, state):
        if self.locked:
            return "It's locked."
        return """You tap a few keys on the keyboard. The computer responds with <br/>
----------<br/>
Congratulations!<br/>
Send me an email! <a target='_blank' href='mailto:game@darksecretsoftware.com'>game@darksecretsoftware.com</a></br>
Follow me on Twitter: <a target='_blank' href='http://twitter.com/#!/TheSandyWalsh'>@TheSandyWalsh</a><br/>
Read my blog: <a target='_blank' href='http://sandywalsh.com'>www.SandyWalsh.com</a><br/>
Look at <a target='_blank' href='https://github.com/SandyWalsh/DarkSecretSoftware'>the source code for this site.</a>"""


class Door(Item):
    def __init__(self):
        super(Door, self).__init__()
        self.locked = True
        self.closed = True

    def name(self):
        return "door"

    def verb_open(self, state):
        if self.locked:
            return "The door is locked."

        if not self.closed:
            return "The door is already open"

        self.closed = False
        room = state.get_room('porch')
        room['exits'][0] = 'foyer'
        return "The door opens effortlessly."

    def verb_close(self, state):
        if self.closed:
            return "The door is already closed"

        self.closed = True
        room = state.get_room('porch')
        room['exits'][0] = None
        return "The door slowly closes and clicks shut."

    def verb_look(self):
        state = ["open", "closed"][self.closed]
        return "A large metal door, painted in a nice neutral color. " \
               "The door is currently %(state)s" % locals()


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
        'exits': [None, None, 'wood shed', 'road']
    },
    'foyer' : {
        'short': 'The foyer of the house.',
        'long': 'You are in the tastefully decorated foyer of the house.',
        'items': [Computer(), ],
        'exits': [None, None, None, 'porch']
    },
    'wood shed' : {
        'short': 'A wood shed.',
        'long': 'You are at the SW corner of the house, near the wood shed.',
        'items': [Axe(), ],
        'exits': ['trampoline', 'porch', None, None]
    },
    'trampoline' : {
        'short': 'In the backyard by the trampoline.',
        'long': 'In the NW corner of the backyard by the trapoline. A zipline runs East to the NE corner of the backyard.',
        'items': [Trampoline(), ZiplineTether()],
        'exits': [None, 'muddy yard', None, 'wood shed']
    },
    'muddy yard' : {
        'short': 'In a very muddy yard.',
        'long': "In a backyard of the house, standing up to your ankles in mud. You can't go any further.",
        'items': [],
        'exits': [None, None, 'trampoline', None]
    },
    'garden' : {
        'short': 'In a small garden in the backyard.',
        'long': 'In the NE corner of the backyard. There is a lovely vegetable garden here. A zipline runs West to the NW corner of the backyard.',
        'items': [Key(),],
        'exits': [None, None, None, None]
    },
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


def check_verb(item, verb_name):
    if hasattr(item, 'verb_%s' % (verb_name, )):
        return item
    raise CantDoThat()
 

def read_item(state, target_name=None, **kwargs):
    target = state.get_target(target_name)
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

    target = state.get_target(target_name)
    check_verb(target, 'look')
    return [(False, target.verb_look()),]


def do_open(state, target_name=None, **kwargs):
    target = state.get_target(target_name)
    check_verb(target, "open")
    return [(False, target.verb_open(state)),]


def do_close(state, target_name=None, **kwargs):
    target = state.get_target(target_name)
    check_verb(target, "close")
    return [(False, target.verb_close(state)),]


def use(state, target_name=None, **kwargs):
    target = state.get_target(target_name)
    check_verb(target, "use")
    return [(False, target.verb_use(state)),]


def take(state, target_name=None, **kwargs):
    target = state.get_target(target_name)
    check_verb(target, "take")
    if not target.verb_take(state):
        return [(False, "You can't take that."),]

    state.remove_item(state.get_room(), target)
    state.add_to_backpack(target)
    return [(False, "You put the %s in your backpack." % target_name),]
    

def drop(state, target_name=None, **kwargs):
    target = state.get_target_from_backpack(target_name)
    check_verb(target, "take")
    if target.verb_take(state):
        return [(False, "You can't drop that."),]

    state.remove_from_backpack(target)
    state.add_item(state.get_room(), target)
    return [(False, "You drop the %s." % target_name),]
    

def inventory(state, **kwargs):
    names = [item.name() for item in state.backpack]
    if not names:
        return [(False, "You are not carrying anything."), ]
    names.sort()
    return [(False, "You are carrying: %s" % ",".join(names)), ]


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
    'use': use,
    'take': take,
    'drop': drop,
    'i': inventory,
    'inventory': inventory,
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
