# coding=utf-8
# Copyright 2020 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""System tests for dags.bq_to_ga_dag."""

import datetime
import json
import os
import pytest

from plugins.pipeline_plugins.utils import system_testing_utils

_AIRFLOW_HOME = 'AIRFLOW_HOME'
_TEST_DAG_NAME = 'tcrm_bq_to_ga'
_TEST_TASK_NAME = 'bq_to_ga_task'
_GCP_PROJECT_ID = 'tcrm-project'
_BQ_PROJECT_ID = 'bq_project_id'
_BQ_DATASET_ID = 'tcrm_bq_to_ga_bq_dataset_id'
_BQ_TABLE_ID = 'tcrm_bq_to_ga_bq_table_id'
_GA_TRACKING_ID = 'ga_tracking_id'
_BQ_CONN_DEFAULT = 'bigquery_default'
_IS_RETRY = _TEST_DAG_NAME + '_is_retry'
_IS_RUN = _TEST_DAG_NAME + '_is_run'


@pytest.fixture(name='configuration')
def fixture_configuration():
  secret_name = 'bq_to_ga'
  secret_ver = '1'
  payload = system_testing_utils.get_payload_from_secret_manager(
      _GCP_PROJECT_ID, secret_name, secret_ver)
  return json.loads(payload)


@pytest.mark.systemtest
@pytest.mark.skipif(os.getenv('TEST_TYPE') != 'SYSTEM',
                    reason='Test isn''t running in system test environment.')
def test_bq_to_ga_dag_system(configuration):
  system_testing_utils.create_or_update_airflow_variable(
      _BQ_DATASET_ID, configuration[_BQ_DATASET_ID])
  system_testing_utils.create_or_update_airflow_variable(
      _BQ_TABLE_ID, configuration[_BQ_TABLE_ID])
  system_testing_utils.create_or_update_airflow_variable(
      _GA_TRACKING_ID, configuration[_GA_TRACKING_ID])
  system_testing_utils.create_or_update_airflow_variable(
      _IS_RETRY, 0)
  system_testing_utils.create_or_update_airflow_variable(
      _IS_RUN, 1)

  project_id = configuration[_BQ_PROJECT_ID]

  system_testing_utils.create_or_update_airflow_gcp_connection(
      _BQ_CONN_DEFAULT, project_id)

  execution_date = system_testing_utils.get_iso8601_date_str(
      datetime.datetime.now())

  system_testing_utils.run_airflow_task(
      _TEST_DAG_NAME,
      _TEST_TASK_NAME,
      execution_date)

  log_content = system_testing_utils.get_latest_task_log(
      _TEST_DAG_NAME,
      _TEST_TASK_NAME,
      execution_date)

  print(log_content)

  assert 'Task exited with return code 0' in log_content
