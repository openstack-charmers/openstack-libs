# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest

from charms.openstack_libs.v0.gnocchi_requires import GnocchiRequires
from ops.charm import CharmBase
from ops.testing import Harness

RELATION_NAME = "metric-service"
RELATION_INTERFACE = "gnocchi"
REGION = "TestRegion"
METADATA = f"""
name: application
requires:
  {RELATION_NAME}:
    interface: {RELATION_INTERFACE}
"""


class ApplicationCharm(CharmBase):
    """Mock application charm to use in unit tests."""

    def __init__(self, *args):
        super().__init__(*args)
        self.metric_service = GnocchiRequires(
            self,
            RELATION_NAME
        )

        self.framework.observe(
            self.metric_service.on.connected,
            self._on_metric_service_connected,
        )
        self.framework.observe(
            self.metric_service.on.ready, self._on_metric_service_ready
        )
        self.framework.observe(
            self.metric_service.on.goneaway,
            self._on_metric_service_goneaway,
        )

    def _on_metric_service_connected(self, _) -> None:
        pass

    def _on_metric_service_ready(self, _) -> None:
        pass

    def _on_metric_service_goneaway(self, _) -> None:
        pass


class TestGnocchiRequires(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(ApplicationCharm, meta=METADATA)
        self.addCleanup(self.harness.cleanup)

    def test_gnocchi_relation(self):
        self.rel_id = self.harness.add_relation(RELATION_NAME, "gnocchi")
        self.harness.add_relation_unit(self.rel_id, "gnocchi/0")
        self.harness.set_leader(True)
        self.harness.begin_with_initial_hooks()

        gnocchi_data = {
            'egress-subnets': '10.0.0.1/32',
            'gnocchi_url': 'https://10.0.0.1:8041',
            'ingress-address': '10.0.0.1',
            'private-address': '10.0.0.1',
        }

        self.harness.update_relation_data(
            self.rel_id,
            "gnocchi/0",
            gnocchi_data,
        )

        self.assertEqual(
            gnocchi_data["gnocchi_url"],
            self.harness.charm.metric_service.gnocchi_url,
        )
