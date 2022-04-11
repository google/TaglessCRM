# coding=utf-8
# Copyright 2022 Google LLC.
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

"""Airflow DAG for uploading Google Ads customer match user list via Google Ads API."""

import os
from typing import Optional

from airflow.models import dag

from dags import base_dag
from plugins.pipeline_plugins.operators import data_connector_operator
from plugins.pipeline_plugins.utils import hook_factory

# Airflow configuration variables.
_AIRFLOW_ENV = 'AIRFLOW_HOME'

# Airflow DAG configurations.
_DAG_NAME = 'tcrm_bq_to_ads_cm_v2'

# BigQuery connection ID. Refer to
# https://cloud.google.com/composer/docs/how-to/managing/connections
# for more details on Managing Airflow connections.
_BQ_CONN_ID = 'bigquery_default'

# Membership lifespan controls how many days that a user's cookie stays on your
# list since its most recent addition to the list. Acceptable range is from 0 to
# 540, and 10000 means no expiration.
_ADS_MEMBERSHIP_LIFESPAN_DAYS = 8

_DEFAULT_API_VERSION = '10'


class BigQueryToAdsCMV2Dag(base_dag.BaseDag):
  """BigQuery to Google Ads Customer Match DAG V2."""

  def create_task(
      self,
      main_dag: Optional[dag.DAG] = None,
      is_retry: bool = False) -> data_connector_operator.DataConnectorOperator:
    """Creates and initializes the main DAG.

    Args:
      main_dag: The dag that the task attaches to.
      is_retry: Whether or not the operator should include a retry task.

    Returns:
      DataConnectorOperator.
    """
    return data_connector_operator.DataConnectorOperator(
        dag_name=_DAG_NAME,
        task_id=self.get_task_id('bq_to_ads_cm', is_retry),
        input_hook=hook_factory.InputHookType.BIG_QUERY,
        output_hook=hook_factory.OutputHookType.GOOGLE_ADS_CUSTOMER_MATCH_V2,
        is_retry=is_retry,
        return_report=self.dag_enable_run_report,
        enable_monitoring=self.dag_enable_monitoring,
        monitoring_dataset=self.monitoring_dataset,
        monitoring_table=self.monitoring_table,
        monitoring_bq_conn_id=self.monitoring_bq_conn_id,
        bq_conn_id=_BQ_CONN_ID,
        bq_dataset_id=self.get_variable_value(_DAG_NAME, 'bq_dataset_id'),
        bq_table_id=self.get_variable_value(_DAG_NAME, 'bq_table_id'),
        api_version=self.get_variable_value(
            _DAG_NAME, 'api_version', fallback_value=_DEFAULT_API_VERSION),
        google_ads_yaml_credentials=self.get_variable_value(
            _DAG_NAME, 'google_ads_yaml_credentials'),
        ads_upload_key_type=self.get_variable_value(
            _DAG_NAME, 'ads_upload_key_type', fallback_value=''),
        ads_cm_app_id=self.get_variable_value(
            _DAG_NAME, 'ads_cm_app_id', fallback_value=None),
        ads_cm_create_list=self.get_variable_value(
            _DAG_NAME,
            'ads_cm_create_list',
            expected_type=bool,
            fallback_value=True),
        ads_cm_membership_lifespan_in_days=self.get_variable_value(
            _DAG_NAME,
            'ads_cm_membership_lifespan_in_days',
            expected_type=int,
            fallback_value=_ADS_MEMBERSHIP_LIFESPAN_DAYS),
        ads_cm_user_list_name=self.get_variable_value(
            _DAG_NAME, 'ads_cm_user_list_name', fallback_value=''),
        dag=main_dag)  # pytype: disable=wrong-arg-types


if os.getenv(_AIRFLOW_ENV):
  dag = BigQueryToAdsCMV2Dag(_DAG_NAME).create_dag()
