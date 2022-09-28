# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest

from charms.openstack_libs.v0.rabbitmq_requires import RabbitMQRequires
from ops.charm import CharmBase
from ops.testing import Harness

RELATION_NAME = "amqp"
RELATION_INTERFACE = "rabbitmq"
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
        self.rabbitmq = RabbitMQRequires(
            self,
            RELATION_NAME,
            username="test",
            vhost="test",
        )

        self.framework.observe(
            self.rabbitmq.on.connected,
            self._on_amqp_connected,
        )

        self.framework.observe(self.rabbitmq.on.ready, self._on_amqp_ready)

        self.framework.observe(
            self.rabbitmq.on.goneaway,
            self._on_amqp_goneaway,
        )

    def _on_amqp_connected(self, _) -> None:
        pass

    def _on_amqp_ready(self, _) -> None:
        pass

    def _on_amqp_goneaway(self, _) -> None:
        pass


class TestRabbitMQRequires(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(ApplicationCharm, meta=METADATA)
        self.addCleanup(self.harness.cleanup)

    def test_rabbitmq_relation(self):
        self.rel_id = self.harness.add_relation(RELATION_NAME, "rabbitmq")
        self.harness.add_relation_unit(self.rel_id, "rabbitmq/0")
        self.harness.set_leader(True)
        self.harness.begin_with_initial_hooks()

        rabbitmq_data = {
            "username": "test",
            "vhost": "test",
            "hostname": "10.0.0.1",
            "password": "strong_password",
            "egress-subnets": "10.0.0.1/32",
            "ingress-address": "10.0.0.1",
            "private-address": "10.0.0.1",
        }

        self.harness.update_relation_data(
            self.rel_id,
            "rabbitmq/0",
            rabbitmq_data,
        )

        self.assertEqual(
            rabbitmq_data["hostname"],
            self.harness.charm.rabbitmq.hostname,
        )

        self.assertEqual(
            rabbitmq_data["password"],
            self.harness.charm.rabbitmq.password,
        )
