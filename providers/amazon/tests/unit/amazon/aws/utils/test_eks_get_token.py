# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

import contextlib
import runpy
from io import StringIO
from unittest import mock

import pytest
import time_machine

from tests_common.test_utils.version_compat import AIRFLOW_V_3_0_PLUS


class TestGetEksToken:
    @mock.patch("airflow.providers.amazon.aws.hooks.eks.EksHook")
    @time_machine.travel("1995-02-14", tick=False)
    @pytest.mark.parametrize(
        "args, expected_aws_conn_id, expected_region_name",
        [
            [
                [
                    "airflow.providers.amazon.aws.utils.eks_get_token",
                    "--region-name",
                    "test-region",
                    "--aws-conn-id",
                    "test-id",
                    "--cluster-name",
                    "test-cluster",
                ],
                "test-id",
                "test-region",
            ],
            [
                [
                    "airflow.providers.amazon.src.airflow.providers.amazon.aws.utils.eks_get_token"
                    if AIRFLOW_V_3_0_PLUS
                    else "airflow.providers.amazon.aws.utils.eks_get_token",
                    "--region-name",
                    "test-region",
                    "--cluster-name",
                    "test-cluster",
                ],
                None,
                "test-region",
            ],
            [
                ["airflow.providers.amazon.aws.utils.eks_get_token", "--cluster-name", "test-cluster"],
                None,
                None,
            ],
        ],
    )
    def test_run(self, mock_eks_hook, args, expected_aws_conn_id, expected_region_name):
        (
            mock_eks_hook.return_value.fetch_access_token_for_cluster.return_value
        ) = "k8s-aws-v1.aHR0cDovL2V4YW1wbGUuY29t"

        with mock.patch("sys.argv", args), contextlib.redirect_stdout(StringIO()) as temp_stdout:
            from airflow.providers.amazon.aws.utils import eks_get_token

            eks_get_token_path = eks_get_token.__file__
            # We are not using run_module because of https://github.com/pytest-dev/pytest/issues/9007
            runpy.run_path(eks_get_token_path, run_name="__main__")
        output = temp_stdout.getvalue()
        token = "token: k8s-aws-v1.aHR0cDovL2V4YW1wbGUuY29t"
        expected_token = output.split(",")[1].strip()
        expected_expiration_timestamp = output.split(",")[0].split(":")[1].strip()
        assert expected_token == token
        assert expected_expiration_timestamp.startswith("1995-02-")
        mock_eks_hook.assert_called_once_with(
            aws_conn_id=expected_aws_conn_id, region_name=expected_region_name
        )
        mock_eks_hook.return_value.fetch_access_token_for_cluster.assert_called_once_with("test-cluster")
