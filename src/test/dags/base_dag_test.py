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

"""Tests for tcrm.dags.base_dag."""

import datetime
import unittest
from unittest import mock

from airflow.exceptions import AirflowException
from airflow.models import dag
from airflow.models import variable

from dags import base_dag
from plugins.pipeline_plugins.operators import error_report_operator


class FakeDag(base_dag.BaseDag):

  def create_task(
      self,
      main_dag: dag.DAG = None,
      is_retry: bool = False) -> error_report_operator.ErrorReportOperator:
    return error_report_operator.ErrorReportOperator(
        task_id='configuration_error',
        error=Exception(),
        dag=main_dag)


class BaseDagTest(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.dag_name = 'test_dag'

    self.airflow_variables = {
        'monitoring_data_days_to_live': '50',
        'dag_name': self.dag_name,
        f'{self.dag_name}_schedule': '@once',
        f'{self.dag_name}_retries': '0',
        f'{self.dag_name}_retry_delay': '3',
        f'{self.dag_name}_is_retry': '1',
        f'{self.dag_name}_is_run': '1',
        f'{self.dag_name}_enable_run_report': '0',
        f'{self.dag_name}_enable_monitoring': '1',
        f'{self.dag_name}_enable_monitoring_cleanup': '1',
        'monitoring_dataset': 'test_monitoring_dataset',
        'monitoring_table': 'test_monitoring_table',
        'monitoring_bq_conn_id': 'test_monitoring_conn',
        'bq_conn_id': 'test_connection',
        'bq_dataset_id': 'test_dataset',
        'bq_table_id': 'test_table',
        'bq_selected_fields': ['f1'],
        'ga_tracking_id': 'UA-12345-67'
    }

    self.addCleanup(mock.patch.stopall)
    self.mock_variable = mock.patch.object(
        variable, 'Variable', autospec=True).start()

    def mock_variable_get(key, default_var):
      if key in self.airflow_variables:
        return self.airflow_variables[key]
      else:
        return default_var
    self.mock_variable.get.side_effect = mock_variable_get

    self.dag = FakeDag(self.dag_name)

  def test_init(self):
    fake_dag = FakeDag(self.dag_name)
    fake_dag.create_task = mock.MagicMock()
    fake_dag._create_cleanup_task = mock.MagicMock()

    test_dag = fake_dag.create_dag()

    self.assertEqual(test_dag.default_args['retries'], base_dag._DAG_RETRIES)
    self.assertEqual(
        test_dag.default_args['retry_delay'], datetime.timedelta(
            minutes=base_dag._DAG_RETRY_DELAY_MINUTES))
    self.assertEqual(test_dag.schedule_interval, base_dag._DAG_SCHEDULE)

  def test_create_dag_successfully(self):
    self.dag.create_task = mock.MagicMock()
    self.dag._create_cleanup_task = mock.MagicMock()

    self.dag.create_dag()

    self.assertEqual(self.dag.create_task.call_count, 2)

  def test_create_dag_failed_due_to_config_error(self):
    self.dag.create_task = mock.MagicMock()
    self.dag.create_task.side_effect = AirflowException()

    self.dag.create_dag()

    self.assertEqual(self.dag.create_task.call_count, 1)

  @mock.patch.object(base_dag.BaseDag, '_create_cleanup_task')
  def test_cleanup_task_called_when_dag_enable_monitoring_cleanup_true(
      self, mock_cleanup_task):

    self.mock_variable.get.side_effect = (
        lambda key, value: self.airflow_variables[key])

    fake_dag = FakeDag(self.dag_name)
    fake_dag.create_dag()

    mock_cleanup_task.assert_called_once()

  def test_get_variable_value_with_prefix(self):
    expected_val = 'prefix_test_table'
    self.airflow_variables[f'{self.dag_name}_bq_table_id'] = expected_val
    actual_val = self.dag.get_variable_value(self.dag_name, 'bq_table_id')
    self.assertEqual(actual_val, expected_val)

  def test_get_variable_value_without_prefix(self):
    actual_val = self.dag.get_variable_value(self.dag_name, 'bq_table_id')
    self.assertEqual(actual_val, 'test_table')

  def test_get_variable_value_return_fallback(self):
    actual_val = self.dag.get_variable_value(self.dag_name, 'fake_key',
                                             fallback_value='fallback')
    self.assertEqual(actual_val, 'fallback')

  def test_get_variable_value_fallback_type_mismatch(self):
    with self.assertRaises(TypeError):
      self.dag.get_variable_value(
          self.dag_name, 'retry_delay', int, fallback_value='5')

  def test_get_variable_value_of_specified_type(self):
    actual_val = self.dag.get_variable_value(
        self.dag_name, 'retry_delay', int, fallback_value=5)
    self.assertEqual(actual_val, 3)

if __name__ == '__main__':
  unittest.main()
