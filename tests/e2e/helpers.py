#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
import logging
from pathlib import Path

import yaml
from pytest_operator.plugin import OpsTest
from juju.model import Model
from juju.controller import Controller


METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())
APP_NAME = METADATA["name"]
ZK_NAME = "zookeeper"

logger = logging.getLogger(__name__)


async def get_or_add_model(ops_test: OpsTest, controller: Controller, model_name: str) -> Model:
    if model_name not in await controller.get_models():
        await controller.add_model(model_name)
        ctl_name = controller.controller_name
        await ops_test.track_model(
            f"{ctl_name}-{model_name}", cloud_name=ctl_name, model_name=model_name, keep=False
        )

    return await controller.get_model(model_name)