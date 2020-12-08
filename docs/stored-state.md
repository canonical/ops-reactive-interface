# Stored State

[StoredState][] can be used just like in Operator framework charms and will use the
same SQLite storage backend as the charms.reactive framework, so that upgrading
charms using these interface API classes from the old framework to the Operator
framework should go smoothly.


## Example

```python
from ops.framework import Object, StoredState


class MyInterface(Object):
    state = StoredState()

    def __init__(self, charm, relation_name):
        super().__init__(charm, relation_name)
        self.relation = charm.model.get_relation(relation_name)
        self.state.set_default(hash=None)

    @property
    def data(self):
        if not (self.relation and self.relation.app):
            return None
        return self.relation.data[self.relation.app].get("data")

    @property
    def _hash(self):
        if not self.data:
            return None
        return md5(str(self.data).encode('utf8')).hexdigest()

    @property
    def is_changed(self):
        return self.state.hash != self._hash

    @is_changed.setter
    def is_changed(self, value):
        if not value:
            self.state.hash = self._hash
```

<!-- Links -->
[StoredState]: https://ops.readthedocs.io/en/latest/#ops.framework.StoredState
