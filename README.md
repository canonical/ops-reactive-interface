# ops-reactive-interface

This library is a helper for developers creating interface protocol API
libraries for charms. The goal is to allow the developer to focus on
implementing the API library using the best practices from the [Operator
framework][] pattern and still enable usage in older charms which have yet to be
transitioned from the [charms.reactive framework][] with minimal additional
developer and resource overhead.

## Usage

All that is required to use this library is to add a bit of info to your
interface protocol API library's `setup.py` to include this as a dependency and
to register your API classes with the role and interface protocol name they
implement. Full details can be found in [the docs](docs), as well as an
[example](docs/example.md) which shows an interface API implementation with
usage by both an Operator framework charm and a charms.reactive charm.


<!-- Links -->
[Operator Framework]: https://github.com/canonical/operator/
[charms.reactive framework]: https://charmsreactive.readthedocs.io/en/latest
