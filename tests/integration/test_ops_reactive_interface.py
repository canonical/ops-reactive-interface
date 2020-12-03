import json


def test_with_charms(ops_charm, reactive_charm, model):
    model.deploy(ops_charm, 2)
    model.deploy(reactive_charm, 2)
    model.wait()
    msgs = _load_msgs(model.status())
    assert msgs['ops-charm'][0] == {
        'taker': {
            'relations': 0,
            'is_changed': False,
            'received': [],
        },
        'sharer': {
            'relations': 1,
            'is_changed': True,
            'received': ['ops-charm/1'],
        },
    }
    assert msgs['ops-charm'][1] == {
        'taker': {
            'relations': 0,
            'is_changed': False,
            'received': [],
        },
        'sharer': {
            'relations': 1,
            'is_changed': True,
            'received': ['ops-charm/0'],
        },
    }
    assert msgs['reactive-charm'][0] == {
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
            'received': ['reactive-charm/1'],
        },
    }
    assert msgs['reactive-charm'][1] == {
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
            'received': ['reactive-charm/0'],
        },
    }


def _load_msgs(status):
    apps = status['applications']
    msgs = {}
    for charm in 'reactive-charm', 'ops-charm':
        msgs[charm] = []
        for name, unit in sorted(apps[charm]['units'].items()):
            msgs[charm].append(json.loads(unit['workload-status']['message']))
    return msgs
