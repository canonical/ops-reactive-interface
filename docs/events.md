# Events

Since the charms.reactive framework does not use the Operator framework's event
system, most events at the charm level will be missing or ignored. However, the
library will ensure that the events for the specific relation endpoints to
which the API instances are bound, as well as the `upgrade_charm` event, will
be emitted, so that the classes can use them as they would in an Operator
framework charm. Additionally, any internal events emitted and observed by the
API classes, as well as deferred events, will function as expected.

Note that these events are processed before the flags for the interface API
instance are managed, meaning those event handlers can be used to manage [stored
state][] which can then be used when managing flags for reactive charm usage.


## Example

```python
import logging

from ops.framework import Object


log = logging.getLogger(__name__)


class MyInterface(Object):
    def __init__(self, charm, relation_name):
        super().__init__(charm, relation_name)
        charm.framework.observe(charm.on[relation_name].relation_changed,
                                self._on_changed)

    def _on_changed(self, event):
        log.info("Change from remote unit: {}".format(event.unit))
```



<!-- Links -->
[stored state]: (stored-state.md)
