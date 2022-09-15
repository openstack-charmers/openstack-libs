# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import unittest

from charms.openstack_libs.v0.keystone_requires import KeystoneRequires
from ops.charm import CharmBase
from ops.testing import Harness

RELATION_NAME = "identity-service"
RELATION_INTERFACE = "keystone"
SERVICE_ENDPOINTS = [
    {
        "service_name": "myservice",
        "internal_url": "http://myservice:80/internal",
        "admin_url": "http://myservice:80/admin",
        "public_url": "http://myservice:80/public",
    }
]
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
        self.identity_service = KeystoneRequires(
            self,
            RELATION_NAME,
            SERVICE_ENDPOINTS,
            REGION,
        )

        self.framework.observe(
            self.identity_service.on.connected,
            self._on_identity_service_connected,
        )
        self.framework.observe(
            self.identity_service.on.ready, self._on_identity_service_ready
        )
        self.framework.observe(
            self.identity_service.on.goneaway,
            self._on_identity_service_goneaway,
        )

    def _on_identity_service_connected(self, _) -> None:
        pass

    def _on_identity_service_ready(self, _) -> None:
        pass

    def _on_identity_service_goneaway(self, _) -> None:
        pass


TEST_APP_DATA_SERVICE_DATA = {
    "admin-auth-url": "http://10.152.183.170:35357",
    "admin-domain-id": "fe53cf5a774e4a70b24db1a4b2b3f3c8",
    "admin-domain-name": "admin_domain",
    "admin-project-id": "bbf750986477488aa4ad12b1ef9e87eb",
    "admin-project-name": "admin",
    "admin-user-id": "854f16e20295428888b1cb3feec49f3d",
    "admin-user-name": "admin",
    "api-version": "3",
    "auth-host": "10.152.183.170",
    "auth-port": "5000",
    "auth-protocol": "http",
    "internal-auth-url": "http://10.5.20.0:80/sunbeam-keystone-k8s",
    "internal-host": "10.152.183.170",
    "internal-port": "5000",
    "internal-protocol": "http",
    "public-auth-url": "http://10.5.20.1:80/sunbeam-keystone-k8s",
    "service-domain-id": "d7445aed1ea8424a8d4dd554b0773474",
    "service-domain-name": "service_domain",
    "service-host": "10.152.183.170",
    "service-password": "password123",
    "service-port": "5000",
    "service-project-id": "b6d1d23302d246c6ad6461f543fda321",
    "service-project-name": "services",
    "service-protocol": "http",
    "service-user-id": "571080913d6243639832274ebdef4f4b",
    "service-user-name": "svc_remote_25c959ced16e4b1684f526476df59354",
}
TEST_UNIT_DATA_SERVICE_DATA = {
    "admin_domain_id": "d0100fc75eaa4172a052da4f976c65d4",
    "admin_project_id": "e1faa6ea8c6e448a9cdd755e2c20a6f4",
    "admin_user_id": "7eae089530a34d38abb5d0a6a5fdd6a5",
    "api_version": "3",
    "auth_host": "10.5.3.154",
    "auth_port": "35357",
    "auth_protocol": "http",
    "egress-subnets": "10.5.3.154/32",
    "ingress-address": "10.5.3.154",
    "internal_host": "10.5.3.154",
    "internal_port": "5000",
    "internal_protocol": "http",
    "private-address": "10.5.3.154",
    "service_domain": "service_domain",
    "service_domain_id": "4e20942773144b258fed19d12a73b00b",
    "service_host": "10.5.3.154",
    "service_password": "mVdB5xM8L2sCn9XSy3swSnwzZWx98C57xnJz5PWHTGr5WT73Fn7TYxJ7Y8h8C78q",
    "service_port": "5000",
    "service_protocol": "http",
    "service_tenant": "services",
    "service_tenant_id": "7fafe059c7bb48609010dba25a6db793",
    "service_username": "aodh",
}


class TestKeystoneRequires(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(ApplicationCharm, meta=METADATA)
        self.addCleanup(self.harness.cleanup)

        self.rel_id = self.harness.add_relation(RELATION_NAME, "keystone")
        self.harness.add_relation_unit(self.rel_id, "keystone/0")
        self.harness.set_leader(True)
        self.harness.begin_with_initial_hooks()

    def test_register_services(self):
        # Forward compatible application scoped presentation
        app_data = self.harness.charm.model.get_relation(
            "identity-service"
        ).data[self.harness.charm.app]
        self.assertEqual(
            app_data["service-endpoints"],
            json.dumps(SERVICE_ENDPOINTS, sort_keys=True),
        )
        self.assertEqual(
            app_data["region"],
            REGION,
        )

        # Backwards compatible unit scoped presentation
        unit_data = self.harness.charm.model.get_relation(
            "identity-service"
        ).data[self.harness.charm.unit]
        self.assertEqual(
            unit_data,
            {
                "service": "myservice",
                "internal_url": "http://myservice:80/internal",
                "admin_url": "http://myservice:80/admin",
                "public_url": "http://myservice:80/public",
                "region": REGION,
            },
        )

    def test_forward_compat(self):
        """Check forwards compatibility with application data."""
        self.harness.update_relation_data(
            self.rel_id,
            "keystone",
            TEST_APP_DATA_SERVICE_DATA,
        )
        for key, value in TEST_APP_DATA_SERVICE_DATA.items():
            self.assertEqual(
                getattr(
                    self.harness.charm.identity_service, key.replace("-", "_")
                ),
                value,
            )

    def test_backward_compat(self):
        """Check backwards compatibility with unit data."""
        self.harness.update_relation_data(
            self.rel_id,
            "keystone/0",
            TEST_UNIT_DATA_SERVICE_DATA,
        )
        # Check remaps
        for (
            new_key,
            old_key,
        ) in KeystoneRequires._backwards_compat_remaps.items():
            self.assertEqual(
                getattr(
                    self.harness.charm.identity_service,
                    new_key.replace("-", "_"),
                ),
                TEST_UNIT_DATA_SERVICE_DATA[old_key],
            )
        # Keys below are new keystone-k8s presented only so should be None
        self.assertIsNone(self.harness.charm.identity_service.public_auth_url)
        self.assertIsNone(
            self.harness.charm.identity_service.internal_auth_url
        )
        self.assertIsNone(self.harness.charm.identity_service.admin_auth_url)

    def test_app_data_priority(self):
        """Ensure that the app data bag takes priority over unit data."""
        self.harness.update_relation_data(
            self.rel_id,
            "keystone",
            TEST_APP_DATA_SERVICE_DATA,
        )
        self.harness.update_relation_data(
            self.rel_id,
            "keystone/0",
            TEST_UNIT_DATA_SERVICE_DATA,
        )

        for key, value in TEST_APP_DATA_SERVICE_DATA.items():
            self.assertEqual(
                getattr(
                    self.harness.charm.identity_service, key.replace("-", "_")
                ),
                value,
            )
