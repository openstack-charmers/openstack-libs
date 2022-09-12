# OpenStack Libraries for Operator Framework Charms

## Description

The `openstack-libs` charm provides a set of [charm libraries] which offers
convenience methods for interacting with charmed OpenStack services.

This charm is **not mean to be deployed** itself and is used as a mechanism
for hosting libraries only.

## Usage

`charmcraft fetch-lib charms.openstack_libs.v0.keystone_requires`

THe following libraries are available in this repository:

- `keystone_requires` - a library for interacting with both legacy
  and new K8S keystone operators.

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines on enhancements to this
charm following best practice guidelines, and `CONTRIBUTING.md` for developer guidance.

[charm libraries]: https://juju.is/docs/sdk/libraries
