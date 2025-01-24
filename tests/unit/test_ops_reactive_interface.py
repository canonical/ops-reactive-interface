import os
from unittest.mock import patch, Mock
from charms.unit_test import MockKV

import pytest

from ops import CharmBase, Handle, Object


def test_without_reactive():
    with pytest.raises(ImportError):
        import ops_reactive_interface  # noqa


MockKV.conn = Mock()


@pytest.mark.dependency()
def test_load(harness):
    from ops_reactive_interface import InterfaceAPIFactory as IAF
    from ori_test import ORITest
    from charms.reactive import set_flag
    IAF.load()
    give = IAF.from_name('give')
    assert isinstance(give, ORITest)
    take = IAF.from_flag('endpoint.take.created')
    assert take is None
    set_flag('endpoint.take.created')
    take = IAF.from_flag('endpoint.take.created')
    assert isinstance(take, ORITest)
    assert give is not take


def test_create_charm(harness):
    import ops_reactive_interface as ori
    IAF = ori.InterfaceAPIFactory
    IAF._charm = None

    with patch.object(ori, '_ModelBackend'):
        with patch.object(ori, 'SQLiteStorage'):
            with patch.object(CharmBase, 'on'):
                charm = IAF._create_charm()
    assert isinstance(charm, CharmBase)
    assert charm.meta.name == 'reactive-charm'


@pytest.mark.dependency(depends=['test_load'])
def test_startup(harness):
    from ops_reactive_interface import InterfaceAPIFactory as IAF
    from charmhelpers.core import hookenv
    from charms.reactive import is_flag_set, register_trigger
    IAF.load()
    charm = IAF._charm
    fw = IAF._charm.framework
    fw.reemit = Mock()

    give = IAF.from_name('give')

    class Observer(Object):
        handle = Handle(charm, 'observer', 'test')
        called = None

        def call(self, event):
            self.called = type(event).__name__

    observer = Observer(charm, "observer")
    fw.observe(charm.on.config_changed, observer.call)
    fw.observe(charm.on.give_relation_created, observer.call)
    fw.observe(charm.on.upgrade_charm, observer.call)
    fw.observe(charm.on.leader_elected, observer.call)

    hookenv.hook_name.return_value = 'config-changed'
    IAF._startup()
    assert fw.reemit.called
    assert not observer.called
    assert not give.is_received
    assert not give.is_changed
    assert not is_flag_set('endpoint.give.created')
    assert not is_flag_set('endpoint.give.received')
    assert register_trigger.called

    rel_id = harness.add_relation('give', 'other')
    assert observer.called == 'RelationCreatedEvent'
    assert not give.received
    assert not give.is_received
    assert not give.is_changed
    assert not is_flag_set('endpoint.give.created')
    assert not is_flag_set('endpoint.give.received')
    observer.called = None

    harness.add_relation_unit(rel_id, 'other/0')
    harness.update_relation_data(rel_id, 'other', {'sent': 'foo'})
    assert not observer.called
    assert give.received
    assert give.is_received
    assert give.is_changed
    assert not is_flag_set('endpoint.give.created')
    assert not is_flag_set('endpoint.give.received')

    hookenv.hook_name.return_value = 'give-relation-created'
    with patch.dict(os.environ, {'JUJU_RELATION': 'give',
                                 'JUJU_RELATION_ID': str(rel_id),
                                 'JUJU_REMOTE_APP': 'other'}):
        IAF._startup()
    assert observer.called == 'RelationCreatedEvent'
    assert give.received
    assert give.is_received
    assert give.is_changed
    assert is_flag_set('endpoint.give.created')
    assert is_flag_set('endpoint.give.received')

    hookenv.hook_name.return_value = 'upgrade-charm'
    observer.called = None
    IAF._startup()
    assert observer.called == 'UpgradeCharmEvent'

    hookenv.hook_name.return_value = 'leader-elected'
    observer.called = None
    IAF._startup()
    assert observer.called == 'LeaderElectedEvent'
