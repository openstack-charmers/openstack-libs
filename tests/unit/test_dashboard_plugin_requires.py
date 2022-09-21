# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import unittest

from charms.openstack_libs.v0.dashboard_plugin_requires import HorizonPlugin
from ops.charm import CharmBase
from ops.testing import Harness

RELATION_NAME = "dashboard"
RELATION_INTERFACE = "dashboard-plugin"
REGION = "TestRegion"
METADATA = f"""
name: application
requires:
  {RELATION_NAME}:
    interface: {RELATION_INTERFACE}
"""


class DashboardPluginCharm(CharmBase):
    """Mock application charm to use in unit tests."""

    def __init__(self, *args):
        super().__init__(*args)
        self.dashboard = HorizonPlugin(
            self, install_packages=["plugin-foo-ui"]
        )

        self.framework.observe(
            self.dashboard.on.available, self._dashboard_available
        )

    def _dashboard_available(self, _) -> None:
        pass


TEST_UNIT_DATA = {
    "openstack_dir": "/foo/bar",
    "bin_path": "/bin/baz",
    "release": "yoga",
}


class TestHorizonDashboardPlugin(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(DashboardPluginCharm, meta=METADATA)
        self.addCleanup(self.harness.cleanup)

        self.rel_id = self.harness.add_relation(
            RELATION_NAME, "openstack-dashboard"
        )
        self.harness.add_relation_unit(self.rel_id, "openstack-dashboard/0")
        self.harness.set_leader(True)
        self.harness.begin_with_initial_hooks()

    def test_register_plugin(self):
        """Tests that the relation will register the plugin when connected."""
        unit_data = self.harness.charm.model.get_relation(RELATION_NAME).data[
            self.harness.charm.unit
        ]
        self.assertEqual(
            unit_data["install-packages"],
            json.dumps(["plugin-foo-ui"], sort_keys=True),
        )

    def test_response_data(self):
        """Tests that the plugin will report openstack release, etc."""
        self.harness.update_relation_data(
            self.rel_id,
            "openstack-dashboard/0",
            TEST_UNIT_DATA,
        )
        for key, value in TEST_UNIT_DATA.items():
            self.assertEqual(getattr(self.harness.charm.dashboard, key), value)
