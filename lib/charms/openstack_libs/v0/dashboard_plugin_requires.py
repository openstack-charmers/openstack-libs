# Copyright 2022 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""# Horizon Dashboard Plugin library.

This library facilitates interactions with the 'classic' OpenStack Dashboard
Machine Charm. This library is used to provide configuration and dependent
package information for this plugin.

Horizon Plugin charms should be created as subordinate charms. These
subordinate charms will run inside the same machine or LXD container that the
horizon service is installed in. The plugin charm should avoid installing any
debian packages directly, as there are complications with upgrade ordering and
compatibility when the OpenStack Dashboard charm is upgraded via an
openstack-upgrade action.

Instead, to ensure consistency, the plugin charm will ask the parent to
install the dependent packages and provide any settings that need to be set
in the Horizon service's local_settings.py configuration file. The data
provided by the subordinate charm is passed verbatim to the local_settings.py.

# Usage

Charms seeking to provide a horizon plugin should import the `HorizonPlugin`
class from this library. The simplest scenario is to just instantiate the
`HorizonPlugin` object and provide the set of debian packages which should be
installed, as below:

    from charms.openstack_libs.v0.dashboard_plugin_requires \
        import HorizonPlugin

    class AwesomeHorizonPluginFoo(CharmBase):
        def __init__(self, *args):
            super().__init__(*args)
            ...
            self.plugin = HorizonPlugin(self, install_packages=['plugin-foo'])
            ...

The first argument ('self') to `HorizonPlugin` is always a reference to the
horizon plugin charm.

The `HorizonPlugin` class provides the information from the OpenStack Horizon
Dashboard charm as well, in the event that they are needed within the plugin.
The plugin charm is provided information regarding the installed OpenStack
release, the bin directory path and the location that the dashboard is
installed to. The plugin charm can access these values as attributes on the
`HorizonPlugin` object.

    ...
    logger.debug(f'Current release is {self.plugin.release}')
    ...

Note, these values are only returned when the relation between plugin charm
and the principal charm exists and the joined events have occurred in the
principal charm.
"""
import json
import logging
from typing import List, Optional

import ops.charm
from ops.framework import EventBase, EventSource, Object, ObjectEvents
from ops.model import Relation

# The unique Charmhub library identifier, never change it
LIBID = "TBD"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 1

logger = logging.getLogger(__name__)


class HorizonConnectedEvent(EventBase):
    """Raised when the OpenStack Horizon Dashboard is connected."""

    pass


class HorizonAvailableEvent(EventBase):
    """Raised when the OpenStack Horizon Dashboard is available."""


class HorizonGoneAwayEvent(EventBase):
    """Raised when the OpenStack Horizon Dashboard is no longer available."""

    pass


class HorizonEvents(ObjectEvents):
    """ObjectEvents class used to provide the `on` for Dashboard events."""

    connected = EventSource(HorizonConnectedEvent)
    available = EventSource(HorizonAvailableEvent)
    goneaway = EventSource(HorizonGoneAwayEvent)


class HorizonPlugin(Object):
    """The client-side API for the OpenStack dashboard interface.

    The DashboardRequires object provides the client-side API for the dashboard
    interface. Charms that require access to the OpenStack dashboard in order
    to provide a plugin extension can use this library to indicate that new
    plugins are available.
    """

    on = HorizonEvents()

    def __init__(
        self,
        charm: ops.charm.CharmBase,
        relation_name: str = "dashboard",
        install_packages: List[str] = None,
        conflicting_packages: Optional[List[str]] = None,
        local_settings: str = "",
        priority: str = None,
    ):
        super().__init__(charm, relation_name)
        self.charm = charm
        self.relation_name = relation_name
        self.install_packages = install_packages
        self.conflicting_packages = conflicting_packages
        self.local_settings = local_settings
        self.priority = priority

        self.framework.observe(
            self.charm.on[relation_name].relation_joined,
            self._on_dashboard_relation_joined,
        )
        self.framework.observe(
            self.charm.on[relation_name].relation_changed,
            self._on_dashboard_relation_changed,
        )
        self.framework.observe(
            self.charm.on[relation_name].relation_broken,
            self._on_dashboard_relation_broken,
        )

    def _on_dashboard_relation_joined(self, event: EventBase):
        """Handles relation joined events for the dashboard relation.

        When the dashboard relation joins, the local plugin info will be
        published to the openstack dashboard charm.

        :param event: the event
        :type event: EventBase
        :return: None
        """
        logging.debug(f"{self.relation_name} relation has joined")
        self.publish_plugin_info(
            self.local_settings,
            self.priority,
            self.install_packages,
            self.conflicting_packages,
            event.relation,
        )
        self.on.connected.emit()

    def _on_dashboard_relation_changed(self, event: EventBase):
        """Handles relation changed events for the dashboard relation.

        When the dashboard relation changes, it may be indicating that there's
        a new OpenStack release or that some other element has changed.
        """
        logging.debug(f"{self.relation_name} relation has changed")
        self.on.available.emit()

    def _on_dashboard_relation_broken(self, event: EventBase):
        """Handles relation departed events for the dashboard relation.

        When the dashboard relation is departed it means the unit/application
        is being removed.

        :param event: the event
        :type event: EventBase
        return: None
        """
        logging.debug(f"{self.relation_name} relation has departed")
        self.on.goneaway.emit()

    @property
    def _relation(self) -> Relation:
        """The shared-db relation."""
        return self.framework.model.get_relation(self.relation_name)

    def publish_plugin_info(
        self,
        local_settings: str,
        priority: str,
        install_packages: Optional[List[str]] = None,
        conflicting_packages: Optional[List[str]] = None,
        relation: Optional[Relation] = None,
    ) -> None:
        """Publish information regarding the plugin to the provider.

        Publishes the dashboard plugin information to the principle charm.
        The principle charm does the installation and maintenance of the
        packages so that it can also manage the upgrades of these packages.

        :param local_settings: a string to be placed into the
            local_settings.py. Note it is placed verbatim into the
            local_settings.py configuration file
        :type local_settings: str
        :param priority: Value used by the principal charm to order the
            configuration blobs when multiple plugin subordinates are present
        :param install_packages: a list of packages that should be installed
            for this plugin
        :type install_packages: Optional[List[str]]
        :param conflicting_packages: a list of packages that conflict with
            this plugin
        :type conflicting_packages: Optional[List[str]]
        :param relation: the relation to set the data on
        :type relation: Relation
        :return: None
        :rtype: None
        """
        rel = relation or self._relation
        # If this is called when there isn't a relation, then just return
        if not rel:
            return

        data = rel.data[self.charm.unit]
        data["local-settings"] = local_settings
        if priority:
            data["priority"] = priority
        if install_packages:
            data["install-packages"] = json.dumps(install_packages)
        if conflicting_packages:
            data["conflicting-packages"] = json.dumps(conflicting_packages)

        rel.data[self.charm.unit].update(data)

    def _get_remote_data(self, key: str) -> Optional[str]:
        """Returns the value for the given key from the relation data.

        As long as *one* of the related units can provide the requested data,
        then that data is returned.

        :param key: the key of the value to retrieve from the relation.
        :type key: str
        :return: the value of the relation data
        :rtype: Optional[str]
        """
        relation = self._relation
        if not relation:
            return None

        for unit in relation.units:
            value = relation.data[unit].get(key)
            if value:
                return value

        return None

    @property
    def openstack_dir(self) -> Optional[str]:
        """Retrieves the openstack_dir property from the principal charm.

        :return: openstack_dir property from principal charm
        :rtype: Optional[str]
        """
        return self._get_remote_data("openstack_dir")

    @property
    def bin_path(self) -> Optional[str]:
        """Retrieves the bin_path property from the principal charm.

        :return: bin_path property from the principal charm
        """
        return self._get_remote_data("bin_path")

    @property
    def release(self) -> Optional[str]:
        """Retrieves the release property from the principal charm.

        :return: release property from the principal charm
        """
        return self._get_remote_data("release")
