# Flags

Charms using the charms.reactive framework work with flags rather than events.
During the statup process of a reactive charm, this library will automatically
manage several flags for your interface API class, and you can optionally define
a method to manage custom flags as well. These flags are the primary way that
the reactive charm will receive messages from your interface API, using
decorators such as [`@when`][] and [`@when_not`][], but they can also just
directly access the API class instances using [`endpoint_from_name`][].

## Automatic Flags

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
`is_changed` property, the `.changed` flag will be set if that property is
`True` and cleared if it is `False`.  Additionally, when the flag is cleared by
a reactive charm, this library will attempt to set the property to `False` (and
ignore failures due to it being a read-only property).  This can be used to
ensure the flag most accurately reflects the salient information about the
relation(s). If no `is_changed` property exists, the flag is set any time a
`{relation_name}-relation-changed` hook is seen and is never cleared
automatically.

## Custom Flags

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
[`@when`]: https://charmsreactive.readthedocs.io/en/latest/charms.reactive.decorators.html#charms.reactive.decorators.when
[`@when_not`]: https://charmsreactive.readthedocs.io/en/latest/charms.reactive.decorators.html#charms.reactive.decorators.when_not
[`endpoint_from_name`]: https://charmsreactive.readthedocs.io/en/latest/charms.reactive.relations.html#charms.reactive.relations.endpoint_from_name
