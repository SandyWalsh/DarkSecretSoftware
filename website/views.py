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
        return "Dark Secret Software Inc. Corporate Office"


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
        'items': [Sign(), ]
    }
}


def get_description(room):
    return room['long']


def get_current_room(request):
    room_name = request.session.get('room', 'sign')
    return ROOMS[room_name]


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
                'items': ', '.join(items)}
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
    """Read an item in the current room or in my inventory."""
    target = get_target(request, target_name)
    check_verb(target, "read")
    return [(False, "%s says '%s'" % (target.name(), target.verb_read())), ]


CMDS = {
    'help': help,
    '?': help,
    'read': read_item,
}


def parse_command(text):
    words = text.split(' ')
    while len(words) < 2:
        words.append(None)
    return tuple(words[:2])


def query(request):
    text = request.POST.get('query', "").lower()
    logger.debug("HELLO")
    verb, target = parse_command(text)
    response = [(False, "Syntax Error"),]
    if verb in CMDS:
        try:
            logger.debug("GOT %s %s" % (verb, target))
            response = CMDS[verb](request, target_name=target, cmds=CMDS)
        except GameException, e:
            response = [(False, e.desc), ]
        except Exception, e:
            response = [(False, e), ]
    return render_to_response('query.html', {'text': response})
