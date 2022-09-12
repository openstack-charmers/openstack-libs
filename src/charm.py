#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""A placeholder charm for the OpenStack libs."""

from ops.charm import CharmBase
from ops.main import main


class OpenStackLibsCharm(CharmBase):
    """Placeholder charm for OpenStack libs."""


if __name__ == "__main__":
    main(OpenStackLibsCharm)
