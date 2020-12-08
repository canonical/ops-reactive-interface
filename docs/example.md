# Example

This example is of a simple [interface](#interface) which lets a [speaking
charm](#speaker-charm-provider) say something to the other, but the [listening
charm](#listener-charm-requirer) is older and uses the charms.reactive
framework.

## Interface

### `setup.py`

```python
from setuptools import setup

setup({
    "name": "speaking-interface",
    "py_modules": ["speaking_interface"],
    "install_requires": [
        "ops>=1.0.0",
        "ops_reactive_interface",
    ],
    "entry_points": {
        "ops_reactive_interface.requires": "speaking = speaking_interface:Listener",
    },
})
```

### `speaking_interface.py`

```python
from ops.framework import Object


class Speaker(Object):
    def __init__(self, charm, relation_name):
        super().__init__(charm, relation_name)
        self.charm = charm
        self.relations = charm.model.relations[relation_name]

    @property
    def can_speak(self):
        # note: only leaders can set app-level relation data
        return self.relations and self.charm.unit.is_leader()

    def say(self, message):
        if self.can_speak:
            for relation in self.relations:
                relation.data[charm.app]["said"] = message


class Listener(Object):
    def __init__(self, charm, relation_name):
        super().__init__(charm, relation_name)
        self.charm = charm
        self.relation_name = relation_name
        self.relation = charm.model.get_relation(relation_name)

    @property
    def heard(self):
        if not self.relation:
            return None
        heard = self.relation.data[self.relation.app].get("said")
        return heard

    def manage_flags(self):
        # This method is optional, and used for setting custom flags.  Also
        # note that this will only be called when used in a reactive charm,
        # and the charms.reactive libraries will not be available in Operator
        # framework charms, so imports need to be considered appropriately.
        from charms.reactive import toggle_flag
        toggle_flag("endpoint.{}.spoken".format(self.relation_name),
                    self.heard)
```

## Speaker Charm (Provider)

### `metadata.yaml`

```yaml
name: speaker
provides:
  listeners:
    interface: speaking
```

### `requirements.txt`

```
ops
speaking-interface
```

### `src/charm.py`

```python
from ops.charm import CharmBase

from speaking_interface import Speaker


class SpeakerCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.speak = Speaker(self, "listeners")
        if speak.can_speak:
            speak.say("hello!")
```

## Listener Charm (Requirer)

### `metadata.yaml`

```yaml
name: listener
requires:
  speaker:
    interface: speaking
    limit: 1
```

### `wheelhouse.txt`

```
speaking-interface
```

### `reactive/listener.py`

```python
from charms.reactive import when, when_not, endpoint_from_name
from charms import layer


@when_not('endpoint.speaker.created')
def speakerless():
    layer.status.blocked('No speaker')


@when('endpoint.speaker.created')
@when_not('endpoint.speaker.spoken')
def listening():
    layer.status.waiting('Waiting for speaker')


@when('endpoint.speaker.spoken')
def heard():
    speaker = endpoint_from_name('speaker')
    layer.status.active('Heard: {}'.format(speaker.heard))
```
