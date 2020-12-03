import json

from charms.reactive import (
    when, when_not,
    endpoint_from_name,
    endpoint_from_flag,
    is_flag_set,
)
from charms import layer

from charmhelpers.core import hookenv


@when('endpoint.give.created', 'leadership.is_leader')
def give():
    giver = endpoint_from_flag('endpoint.give.created')
    giver.give(hookenv.service_name())


@when('endpoint.share.created', 'leadership.is_leader')
def share(endpoint):
    sharer = endpoint_from_flag('endpoint.share.created')
    sharer.give(hookenv.local_unit())


@when_not('foo')
def debug():
    taker = endpoint_from_name('take')
    sharer = endpoint_from_name('share')
    hookenv.log(f'taker: {taker}')
    hookenv.log(f'sharer: {sharer}')
    from ops_reactive_interface import InterfaceAPIFactory as IAF
    hookenv.log(f'IAF: {IAF._relation_apis}')


@hookenv.atexit
def set_status():
    taker = endpoint_from_name('take')
    sharer = endpoint_from_name('share')
    hookenv.log(f'taker: {taker}')
    hookenv.log(f'sharer: {sharer}')
    from ops_reactive_interface import InterfaceAPIFactory as IAF
    hookenv.log(f'IAF: {IAF._relation_apis}')
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
