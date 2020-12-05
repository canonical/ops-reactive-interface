import json


def test_with_charms(ops_charm, reactive_charm, model):
    # first deploy with peers, but no relation
    model.deploy(ops_charm, 2)
    model.deploy(reactive_charm, 2)
    model.wait()
    msgs = _load_msgs(model.status())
    expected = {
        'ops-charm': {
            'taker': {
                'relations': 0,
                'is_changed': False,
                'received': [],
            },
            'sharer': {
                'relations': 1,
                'is_changed': True,
                'received': ['ops-charm'],
            },
        },
        'reactive-charm': {
            'taker': {
                'relations': 0,
                'is_changed': False,
                'is_changed_flag': False,
                'received': [],
            },
            'sharer': {
                'relations': 1,
                'is_changed': True,
                'is_changed_flag': True,
                'received': ['reactive-charm'],
            },
        },
    }
    for charm in ('ops-charm', 'reactive-charm'):
        for unit_name, msg in msgs[charm].items():
            assert msg == expected[charm]

    # then add first relation
    model.add_relation('ops-charm:give', 'reactive-charm:take')
    model.wait()
    msgs = _load_msgs(model.status())
    expected['reactive-charm']['taker'].update({
        'relations': 1,
        'is_changed': True,
        'is_changed_flag': True,
        'received': ['ops-charm'],
    })
    for charm in ('ops-charm', 'reactive-charm'):
        for unit_name, msg in msgs[charm].items():
            assert msg == expected[charm]

    # then add reverse relation
    model.add_relation('ops-charm:take', 'reactive-charm:give')
    model.wait()
    msgs = _load_msgs(model.status())
    expected['ops-charm']['taker'].update({
        'relations': 1,
        'is_changed': True,
        'received': ['reactive-charm'],
    })
    for charm in ('ops-charm', 'reactive-charm'):
        for unit_name, msg in msgs[charm].items():
            assert msg == expected[charm]


def _load_msgs(status):
    apps = status['applications']
    msgs = {}
    for charm in 'reactive-charm', 'ops-charm':
        msgs[charm] = {}
        for name, unit in sorted(apps[charm]['units'].items()):
            msgs[charm][name] = json.loads(unit['workload-status']['message'])
    return msgs
