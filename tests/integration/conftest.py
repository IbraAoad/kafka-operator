import pytest
from pytest_operator.plugin import OpsTest


@pytest.fixture(scope="module")
def usernames():
    print("USERNAMEs")
    return set()


@pytest.fixture(scope="module")
async def app_charm(ops_test: OpsTest):
    """Build the application charm."""
    charm = await ops_test.build_charm("tests/integration/app-charm")
    return charm
