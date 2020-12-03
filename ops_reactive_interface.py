from pathlib import Path

from ops.charm import CharmBase, CharmMeta
from ops.framework import Framework
from ops.main import (
    CHARM_STATE_FILE,
    _get_event_args,
)
from ops.model import Model, _ModelBackend
from ops.storage import SQLiteStorage

# NB: This module should only be imported by the charms.reactive framework
#     detecting its entry point and loading it. When used in an operator
#     framework charm, we don't want to have it pull in the charms.reactive
#     library or its many dependencies. So even though we assume they are
#     installed here, they are *not* included in the dependency list in
#     setup.py.
from charms.reactive import (
    is_flag_set,
    register_trigger,
    set_flag,
    toggle_flag,
)
from charmhelpers.core import hookenv

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points


class InterfaceAPIFactory:
    _relation_apis = {}
    _charm = None

    @classmethod
    def load(cls):
        charm = cls._create_charm()
        eps = entry_points()
        for role in ('provides', 'requires', 'peers'):
            role_endpoints = getattr(charm.meta, role)
            for ep in eps.get('ops_reactive_interface.{}'.format(role), []):
                interface_name = ep.name
                for endpoint_name, endpoint_meta in role_endpoints.items():
                    if endpoint_meta.interface_name == interface_name:
                        rel_api_class = ep.load()
                        rel_api_inst = rel_api_class(charm, endpoint_name)
                        cls._relation_apis[endpoint_name] = rel_api_inst

    @classmethod
    def from_name(cls, relation_name):
        return cls._relation_apis.get(relation_name)

    @classmethod
    def from_flag(cls, flag):
        if not is_flag_set(flag) or '.' not in flag:
            return None
        parts = flag.split('.')
        if parts[0] == 'endpoint':
            return cls.from_name(parts[1])
        else:
            return cls.from_name(parts[0])

    @classmethod
    def _create_charm(cls):
        if cls._charm is None:
            charm_dir = Path(hookenv.charm_dir())
            charm_state_path = charm_dir / CHARM_STATE_FILE
            store = SQLiteStorage(charm_state_path)
            meta = CharmMeta(hookenv.metadata())
            model = Model(meta, _ModelBackend())
            framework = Framework(store, charm_dir, meta, model)
            framework.set_breakpointhook()
            cls._charm = CharmBase(framework)
        return cls._charm

    @classmethod
    def _startup(cls):
        for relation_name, relation_api in cls._relation_apis.items():
            cls._manage_automatic_flags(relation_name, relation_api)
            if hasattr(relation_api, 'manage_flags'):
                relation_api.manage_flags()

        cls._charm.framework.reemit()

        hook_name = hookenv.hook_name()
        if '-relation-' not in hook_name:
            return
        hook_parts = hook_name.rsplit('-', 2)
        relation_name = hook_parts[0]
        if relation_name not in cls._relation_apis:
            return
        event_name = hook_name.replace('-', '_')
        event = getattr(cls._charm.on, event_name)
        args, kwargs = _get_event_args(cls._charm, event)
        event.emit(*args, **kwargs)

    @classmethod
    def _manage_automatic_flags(cls, relation_name, relation_api):
        prefix = 'endpoint.' + relation_name
        relations = cls._charm.model.relations[relation_name]
        toggle_flag(prefix + '.created', len(relations) > 0)
        toggle_flag(prefix + '.joined', any(len(rel.units) > 0
                                            for rel in relations))
        if hasattr(relation_api, 'is_changed'):
            toggle_flag(prefix + '.changed', relation_api.is_changed)
            register_trigger(when_not=prefix + '.changed',
                             callback=lambda: setattr(relation_api,
                                                      'is_changed',
                                                      False))
        elif hookenv.hook_name() == relation_name + '-relation-changed':
            set_flag(prefix + '.changed')

    @classmethod
    def _shutdown(cls):
        cls._charm.framework.commit()
        cls._charm.framework.close()


hookenv.atstart(InterfaceAPIFactory._startup)
hookenv.atexit(InterfaceAPIFactory._shutdown)
