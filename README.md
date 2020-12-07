# ops-reactive-interface

Helper for operator-framework focused interface libraries to be used in
reactive charms.

Moving forward, we really want all new development using the much better
[Operator Framework][], but during the transition period new and converted
charms will need to be able to share relations with older charms. This makes
creating new or converting interface API code difficult, as it generally means
having to maintain two separate copies of the logic and keeping them in sync.

This library allows an interface API library written for the new framework to be
used directly by legacy charms still using the [charms.reactive framework][]
with minimal additional overhead on the part of the interface API author.

## Usage

When included as a dependency of your interface API library, your library can
register one or more classes using [entry points][] to implement the interface
for a given role. It can then be used using the typical patterns for charms
using either the Operator framework or the charms.reactive framework.

### Registration

To register your interface API classes, your `setup.py` will need to do two
things:

* Include it in the `install_requires` list as a dependency
* Add [entry points][] for one or more of the following groups:
  * `ops_reactive_interface.provides`
  * `ops_reactive_interface.requires`
  * `ops_reactive_interface.peers`

The name of the entry point should be the name of the interface protocol (i.e.,
the value of the `interface:` field used in a charm's `metadata.yaml`) and the
value should point to the class which implements that role for the interface.

For example:

```python
from setuptools import setup

setup({
    "name": "my-interface",
    "py_modules": ["my_interface"],
    "install_requires": [
        "ops>=1.0.0",
        "ops_reactive_interface",
    ],
    "entry_points": {
        "ops_reactive_interface.provides": "my-interface = my_interface:MyProvides",
        "ops_reactive_interface.requires": "my-interface = my_interface:MyRequires",
    },
})
```

Each registered class must be able to be instantiated with just the charm
instance and the relation endpoint name as the only required positional
parameters, as this will be done automatically when used by a charm based on the
charms.reactive framework, but additional optional parameters can be allowed for
use in Operator framework based charms.

### Operator Framework Usage

The interface API classes can then be used normally in Operator framework
charms, by including it in the charm's `requirements.txt` and creating an
instance during the charm class' `__init__`. When used in a charm using the
Operator framework, no additional dependencies or overhead will be incurred.  

For example, given the following `metadata.yaml`:

```yaml
name: my-database
provides:
  clients:
    interface: my-interface
```

The associated charm might look something like:

```python
from ops.charm import CharmBase
from my_interface import MyProvides


class MyDB(CharmBase):
    def __init__(self, *args:
        super().__init__(*args)
        self.clients = MyProvides(self, 'clients')
        self.framework.observe(self.clients.on.request, self._handle_request)

    def _handle_request(self, event):
        ...
```

### Reactive Framework Usage

For charms based on the charms.reactive, the interface API library should be
included in the charm's `wheelhouse.txt` file rather than being included as an
interface layer. Then, during the startup of each hook, an instance of the
registered classes will be automatically created using a placeholder `CharmBase`
instance and the appropriate relation endpoint name.

From there, the charm will interact with the interface API class in the typical
fashion, reacting to the appropriate flags and retrieving instances of the class
for a given relation endpoint using with [`endpoint_from_name`][] or
[`endpoint_from_flag`][].

For example, given the following `metadata.yaml`:

```yaml
name: my-db-client
requires:
  db:
    interface: my-interface
    limit: 1
```

The associate charm might look something like:

```python
from charms.reactive import (
    clear_flag,
    endpoint_from_name,
    set_flag,
    when,
    when_any,
    when_not,
)


@when("endpoint.db.created")
@when_not("my-db-client.db.requested")
def request_db():
    db = endpoint_from_name("db")
    db.request()
    set_flag("my-db-client.db.requested")


@when_any("endpoint.db.ready",
          "endpoint.db.changed")
def use_db():
    db = endpoint_from_name("db")
    if db.is_changed:
        my_app.set_db(db.host, db.user, db.password, db.name)
        clear_flag("endpoint.db.changed")
```

#### Events

Although most events will not be emitted or will be ignored in a charm based on
the charms.reactive framework, the relation hooks relevant to the relation
endpoints using the interface protocol registered for your class will emit the
appropriate relation event on the placeholder charm once all instances have been
setup. Thus, your interface API class can observe these events and handle them
appropriately, just as they would within an Operator framework charm. Any
additional events emitted by those handlers which have observers (such as custom
internal class events), as well as any deferred events should also work as you
would expect in an Operator framework charm.

Note that these events are processed before the flags for the interface API
instance are managed, meaning those event handlers can be used to manage stored
state which can then be used when managing flags for reactive charm usage.

#### Stored State

Stored state can be used just like in Operator framework charms and will use the
same SQLite storage backend as the charms.reactive framework.

#### Automatic Flags

The following flags will be automatically managed during the startup of each
hook for each relation endpoint:

* `endpoint.{relation_name}.created` Set when any relation is created on the
  endpoint (i.e., there is at least one relation ID available). Cleared when all
  relations are broken (i.e., no relation IDs are available).

* `endpoint.{relation_name}.joined` Set when any relation is joined on the
  endpoint (i.e., there is at least one related unit on any available relation
  ID). Cleared when no relations are joined (i.e., no relation IDs are available
  or no related units are available on any relation IDs).

* `endpoint.{relation_name}.changed` Set when relation data has changed.
  [&ddagger;](#note-changed-flag)

<span id="note-changed-flag">&ddagger;</span>: If the interface API class has an
`is_changed` property, the `.changed` flag will be set whenever that is `True`
and cleared whenever it is `False`.  Additionally, when the flag is cleared by a
reactive charm, this library will attempt to set the property to `False` (and
ignore failures due to it being a read-only property).  This can be used to
ensure the flag most accurately reflects the salient information about the
relation(s). Otherwise, the flag is set any time a
`{relation_name}-relation-changed` hook is seen and is never cleared
automatically.

#### Custom Flags

A registered interface API class can optionally also define a `manage_flags`
method which will be called immediately after the automatic are managed, so that
the instance can set or clear any other relation-specific flags. Note that this
method will only ever be called when the interface API library is used from
within a charms.reactive charm, and none of the charms.reactive libraries are
expected to be available otherwise, so imports from charms.reactive,
charmhelpers, or any of the other typical reactive style charm dependencies
should only be done within this method, or within a `try` / `except` block to
account for them being unavailable.



<!-- Links -->
[Operator Framework]: https://github.com/canonical/operator/
[charms.reactive framework]: https://charmsreactive.readthedocs.io/en/latest
[entry points]: https://packaging.python.org/specifications/entry-points/
[`endpoint_from_name`]: https://charmsreactive.readthedocs.io/en/latest/charms.reactive.relations.html#charms.reactive.relations.endpoint_from_name
[`endpoint_from_flag`]: https://charmsreactive.readthedocs.io/en/latest/charms.reactive.relations.html#charms.reactive.relations.endpoint_from_flag
