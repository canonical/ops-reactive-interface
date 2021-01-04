# Registration

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

Each registered class must be able to be instantiated with just the charm
instance and the relation endpoint name as the only required positional
parameters, as this will be done automatically when used by a charm based on the
charms.reactive framework. Additional optional parameters can be allowed, for
use in Operator framework based charms, but it is probably best to keep the
interfaces consistent.

## Example

```python
setup({
    "install_requires": [
        "ops>=1.0.0",
        "ops_reactive_interface",
    ],
    "entry_points": {
        "ops_reactive_interface.provides": "my-interface = my_interface:Provides",
        "ops_reactive_interface.requires": "my-interface = my_interface:Requires",
        "ops_reactive_interface.peers": "my-interface = my_interface:Peers",
    },
})
```

<!-- Links -->
[entry points]: https://packaging.python.org/specifications/entry-points/
