# # Copyright 2022 Canonical Ltd.
# # See LICENSE file for licensing details.
# from unittest.mock import patch

import pytest
from charm import KafkaCharm
from interface_tester import InterfaceTester

@pytest.fixture
def interface_tester(interface_tester: InterfaceTester):
    interface_tester.configure(
        charm_type=KafkaCharm,
    )
    yield interface_tester