#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

import logging
import subprocess
from typing import Tuple

from ops.charm import CharmBase
from ops.main import main
from ops.model import MaintenanceStatus, ActiveStatus, BlockedStatus
from juju.model import Model
from juju.unit import Unit
from juju.application import Application
import asyncio

from packages import install_packages

logger = logging.getLogger(__name__)


class KafkaCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.name = "kafka"

        self.framework.observe(getattr(self.on, "install"), self._on_install)
        # self.framework.observe(getattr(self.on, "leader_elected"), self._on_leader_elected)
        # self.framework.observe(
        #     getattr(self.on, "cluster_relation_joined"), self._on_cluster_relation_joined
        # )
        self.framework.observe(getattr(self.on, "config_changed"), self._on_config_changed)

    @property
    def _relation(self):
        return self.model.get_relation("cluster")

    def _on_install(self, _) -> None:
        self.unit.status = MaintenanceStatus("installing packages")
        install_packages()

    # def _on_leader_elected(self, _):
    #     zookeeper_units = [
    #         unit_name
    #         for unit_name in self._relation.data[self.model.app]
    #         if self._relation.data[self.model.app][unit_name]["unit-type"] == "zookeeper"
    #     ]
    #
    #     if self.unit.is_leader() and len(zookeeper_units) != self.config["num-zookeeper-units"]:
    #
    #         # HERE BE DRAGONS
    #         loop = asyncio.get_event_loop()
    #         new_zookeeper_units = loop.run_until_complete(
    #             self._add_zookeeper_units(num_zookeeper_units=self.config["num-zookeeper-units"])
    #         )
    #         
    #         # Labelling new ZK units
    #         for zookeeper_unit in new_zookeeper_units:
    #             self._relation.data[self.model.app][zookeeper_unit.entity_id][
    #                 "unit-type"
    #             ] = "zookeeper"
    
    def _on_cluster_relation_joined(self, event):
        if self.unit.is_leader():
            # Defaulting to kafka for new units
            event.data[self.model.app][event.unit.name]["unit-type"] = self.config["unit-type"]

    def _on_config_changed(self, _) -> None:
        self._start_services()

        if not isinstance(self.unit.status, BlockedStatus):
            self.unit.status = ActiveStatus()

    def _start_services(self) -> None:
        if self._relation.data[self.model.app][self.unit.name]["unit-type"] == "zookeeper":

            logger.info("stopping default kafka service")
            kafka_stopped = self._run_command(["sudo", "snap", "stop", "kafka"])
            if not kafka_stopped:
                self.unit.status = BlockedStatus("failed to stop default kafka service")

            logger.info("starting zookeeper service")
            zookeeper_started = self._run_command(["sudo", "kafka.zookeeper"])
            if not zookeeper_started:
                self.unit.status = BlockedStatus("failed to start zookeeper service")
        else:
            logger.debug("unit is kafka, skipping")
    #
    # # HERE BE HERESY
    # async def _add_zookeeper_units(self, num_zookeeper_units=3) -> Tuple:
    #     model = Model()
    #     await model.connect_current()
    #     app = Application(entity_id=self.name, model=model)
    #     new_zookeeper_units = await app.add_units(count=num_zookeeper_units)
    #     return new_zookeeper_units or ()
    #
    def _run_command(self, cmd: list) -> bool:
        proc = subprocess.Popen(cmd)
        for line in iter(getattr(proc.stdout, "readline"), ""):
            logger.debug(line)
        proc.wait()
        return proc.returncode == 0


if __name__ == "__main__":
    main(KafkaCharm)
