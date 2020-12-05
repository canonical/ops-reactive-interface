import json

from charms.reactive import (
    when,
    endpoint_from_name,
    endpoint_from_flag,
    is_flag_set,
)
from charms import layer

from charmhelpers.core import hookenv


@when('endpoint.give.created', 'leadership.is_leader')
def give():
    giver = endpoint_from_flag('endpoint.give.created')
    giver.send(hookenv.service_name())


@when('endpoint.share.created', 'leadership.is_leader')
def share(endpoint):
    sharer = endpoint_from_flag('endpoint.share.created')
    sharer.send(hookenv.service_name())


@hookenv.atexit
def set_status():
    taker = endpoint_from_name('take')
    sharer = endpoint_from_name('share')
    layer.status.active(json.dumps({
        'taker': {
            'relations': len(taker.relations),
            'is_changed': taker.is_changed,
            'is_changed_flag': is_flag_set('endpoint.take.changed'),
            'received': taker.received,
        },
        'sharer': {
            'relations': len(sharer.relations),
            'is_changed': sharer.is_changed,
            'is_changed_flag': is_flag_set('endpoint.share.changed'),
            'received': sharer.received,
        },
    }))
