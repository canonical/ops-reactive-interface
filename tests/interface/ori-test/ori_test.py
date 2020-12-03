from hashlib import md5

from ops.framework import (
    Object,
    StoredState,
)


class ORITest(Object):
    state = StoredState()

    def __init__(self, charm, relation_name):
        super().__init__(charm, relation_name)
        self.charm = charm
        self.relation_name = relation_name
        self.state.set_default(hash=None)

    @property
    def relations(self):
        return self.charm.model.relations[self.relation_name]

    def send(self, value):
        for relation in self.relations:
            relation.data[self.charm.app]['sent'] = value

    @property
    def received(self):
        return [relation.data[relation.app]['sent']
                for relation in self.relations
                if relation.data.get(relation.app, {}).get('sent')]

    @property
    def is_received(self):
        return len(self.received) > 0

    @property
    def is_changed(self):
        return self.state.hash != self._hash

    @is_changed.setter
    def is_changed(self, value):
        if not value:
            self.state.hash = self._hash

    @property
    def _hash(self):
        if not self.received:
            return None
        return md5(str(self.received).encode('utf8')).hexdigest()

    def manage_flags(self):
        # This will only be called when used in a reactive charm.
        from charms.reactive import toggle_flag
        prefix = f'endpoint.{self.relation_name}'
        toggle_flag(f'{prefix}.received', self.is_received)
        toggle_flag(f'{prefix}.changed', self.is_changed)
