# python3
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

"""Airflow DAG for TCRM workflow.

This DAG will transfer data from Google Cloud Storage to Customer Match Ads.

This DAG relies on these Airflow variables:
* `ads_cm_user_list_name`:      The Customer MAtch user list name.
                                Ex: `my_list`.
* `ads_credentials`:            A dict of Adwords client ids and tokens.
                                Reference for desired format:
                                https://developers.google.com/adwords/api/docs/guides/first-api-call
* `ads_upload_key_type`:        The upload key type. Refer to
                                ads_hook.UploadKeyType for more information.
* `ads_cm_app_id`:              An ID string required for creating a new list if
                                upload_key_type is MOBILE_ADVERTISING_ID.
* `ads_cm_create_list`:         A flag to enable a new list creation if a list
                                called user_list_name doesn't exist.
* `ads_cm_membership_lifespan`: Number of days a user's cookie stays. Refer to
                                ads_hook.GoogleAdsHook for details.
* `gcs_bucket_name`:            Google Cloud Storage bucket name.
                                Ex: 'my_bucket'.
* `gcs_bucket_prefix`:          Google Cloud Storage folder name where data is
                                stored. Ex: 'my_folder'.
Refer to https://airflow.apache.org/concepts.html#variables for more on Airflow
Variables.
"""

import os
from typing import Optional

from airflow.models import dag

from dags import base_dag
from plugins.pipeline_plugins.operators import data_connector_operator
from plugins.pipeline_plugins.utils import hook_factory

# Airflow configuration variables.
_AIRFLOW_ENV = 'AIRFLOW_HOME'

# Airflow DAG configuration.
_DAG_NAME = 'tcrm_gcs_to_ads_cm'

# GCS configuration.
_GCS_CONTENT_TYPE = 'JSON'

# Membership lifespan controls how many days that a user's cookie stays on your
# list since its most recent addition to the list. Acceptable range is from 0 to
# 10000, and 10000 means no expiration.
_ADS_MEMBERSHIP_LIFESPAN_DAYS = 8


class GCSToAdsCMDag(base_dag.BaseDag):
  """Cloud Storage to Google Analytics DAG."""

  def create_task(
      self,
      main_dag: Optional[dag.DAG] = None,
      is_retry: bool = False) -> data_connector_operator.DataConnectorOperator:
    """Creates and initializes the main DAG.

    Args:
      main_dag: The dag that the task attaches to.
      is_retry: Whether or not the operator should includ a retry task.

    Returns:
      DataConnectorOperator.
    """
    return data_connector_operator.DataConnectorOperator(
        dag_name=_DAG_NAME,
        task_id=self.get_task_id('gcs_to_ads_cm', is_retry),
        input_hook=hook_factory.InputHookType.GOOGLE_CLOUD_STORAGE,
        output_hook=hook_factory.OutputHookType.GOOGLE_ADS_CUSTOMER_MATCH,
        is_retry=is_retry,
        return_report=self.dag_enable_run_report,
        enable_monitoring=self.dag_enable_monitoring,
        monitoring_dataset=self.monitoring_dataset,
        monitoring_table=self.monitoring_table,
        monitoring_bq_conn_id=self.monitoring_bq_conn_id,
        gcs_bucket=self.get_variable_value(
            _DAG_NAME, 'gcs_bucket_name', fallback_value=''),
        gcs_content_type=self.get_variable_value(
            _DAG_NAME, 'gcs_content_type',
            fallback_value=_GCS_CONTENT_TYPE).upper(),
        gcs_prefix=self.get_variable_value(
            _DAG_NAME, 'gcs_bucket_prefix', fallback_value=''),
        ads_credentials=self.get_variable_value(_DAG_NAME, 'ads_credentials'),
        ads_upload_key_type=self.get_variable_value(
            _DAG_NAME, 'ads_upload_key_type', fallback_value=''),
        ads_cm_app_id=self.get_variable_value(
            _DAG_NAME, 'ads_cm_app_id', fallback_value=None),
        ads_cm_create_list=self.get_variable_value(
            _DAG_NAME,
            'ads_cm_create_list',
            expected_type=bool,
            fallback_value=True),
        ads_cm_membership_lifespan=self.get_variable_value(
            _DAG_NAME,
            'ads_cm_membership_lifespan',
            expected_type=int,
            fallback_value=_ADS_MEMBERSHIP_LIFESPAN_DAYS),
        ads_cm_user_list_name=self.get_variable_value(
            _DAG_NAME, 'ads_cm_user_list_name', fallback_value=''),
        dag=main_dag)


if os.getenv(_AIRFLOW_ENV):
  dag = GCSToAdsCMDag(_DAG_NAME).create_dag()
