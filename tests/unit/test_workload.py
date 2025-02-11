#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from unittest.mock import mock_open, patch

import pytest
from charms.operator_libs_linux.v1.snap import SnapError

from workload import KafkaWorkload


def test_run_bin_command_args(patched_exec):
    """Checks KAFKA_OPTS env-var and zk-tls flag present in all snap commands."""
    KafkaWorkload().run_bin_command(bin_keyword="configs", bin_args=["--list"], opts=["-Djava"])

    assert "charmed-kafka.configs" in patched_exec.call_args.args[0].split()
    assert "-Djava" == patched_exec.call_args.args[0].split()[0]
    assert "--list" == patched_exec.call_args.args[0].split()[-1]


def test_get_service_pid_raises():
    """Checks get_service_pid raises if PID cannot be found."""
    with (
        patch(
            "builtins.open",
            new_callable=mock_open,
            read_data="0::/system.slice/snap.charmed-zookeeper.daemon.service",
        ),
        patch("subprocess.check_output", return_value="123"),
        pytest.raises(SnapError),
    ):
        KafkaWorkload().get_service_pid()


def test_get_service_pid_raises_no_pid():
    """Checks get_service_pid raises if PID cannot be found."""
    with (
        patch("subprocess.check_output", return_value=""),
        pytest.raises(SnapError),
    ):
        KafkaWorkload().get_service_pid()
