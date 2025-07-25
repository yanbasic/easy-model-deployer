import boto3
from typing import Dict, List, Optional
import concurrent.futures
import time
from functools import lru_cache

from emd.constants import CODEPIPELINE_NAME, MODEL_DEFAULT_TAG
from emd.utils.aws_service_utils import check_stack_status
from emd.models import Model
from emd.utils.aws_service_utils import (
    check_stack_status,
    get_pipeline_active_executions,
    get_model_stacks,
    check_env_stack_exist_and_complete
)
from emd.utils.aws_service_utils import get_account_id
from emd.utils.aws_service_utils import get_current_region
from emd.utils.logger_utils import get_logger

# Add constants for parallel execution handling
PARALLEL_EXECUTION_SEPARATOR = "__"
MAX_PARALLEL_EXECUTIONS_PER_MODEL = 5  # Safety limit

logger = get_logger(__name__)
def get_pipeline_execution_status(
        pipeline_execution_id: str,
        pipeline_name: str = CODEPIPELINE_NAME,
        region=None
    ):
    if region is None:
        region = get_current_region()

    client = boto3.client('codepipeline', region_name=region)

    try:
        response = client.get_pipeline_execution(
            pipelineName=pipeline_name,
            pipelineExecutionId=pipeline_execution_id
        )
    except client.exceptions.PipelineExecutionNotFoundException:
        return {
            "status": "NotFound",
            "status_code": 0,
            "is_succeeded": False,
            "stage_name": None,
            "status_summary": "Pipeline execution not found",
            "pipeline_execution_id": pipeline_execution_id
        }

    execution = response['pipelineExecution']
    status = execution['status']
    status_summary = execution.get('statusSummary', "")

    ret = {
        "status": status,
        "status_code": 1,
        "is_succeeded": status == 'Succeeded',
        "stage_name": None,
        "status_summary": status_summary,
        "pipeline_execution_id": pipeline_execution_id  # Add execution ID to response
    }

    if status in ['Stopped', 'Succeeded', 'Cancelled', "Failed"]:
        ret['status_code'] = 0

    # Get current stage information for this specific execution
    try:
        active_executuion_infos = get_pipeline_active_executions(
            pipeline_name=pipeline_name,
            client=client,
            return_dict=True,
            filter_stoped=False,
            filter_failed=False
        )

        if pipeline_execution_id in active_executuion_infos:
            execution_info = active_executuion_infos[pipeline_execution_id]
            ret['stage_name'] = execution_info['stage_name']

            # Add additional parallel execution context
            ret['model_id'] = execution_info['model_id']
            ret['model_tag'] = execution_info['model_tag']
            ret['instance_type'] = execution_info['instance_type']
            ret['engine_type'] = execution_info['engine_type']
            ret['service_type'] = execution_info['service_type']

    except Exception as e:
        # Don't fail the whole status check if stage info fails
        ret['stage_name'] = f"Error getting stage info: {str(e)}"

    return ret


def get_destroy_status(stack_name:str):
    stach_status = check_stack_status(stack_name)
    status = stach_status.status
    if not stach_status.is_exist:
        return {
             "status_code": 0,
             "status": status,
             "is_succeeded":True
        }
    if stach_status.status == "DELETE_FAILED":
        return {
             "status_code": 0,
             "is_succeeded":False,
             "status": status,
        }
    return {
             "status_code": 1,
             "is_succeeded":False,
             "status": status,
        }


def get_model_status(model_id: str = None, model_tag=MODEL_DEFAULT_TAG):
    check_env_stack_exist_and_complete()
    active_executuion_infos = get_pipeline_active_executions(
        pipeline_name=CODEPIPELINE_NAME,
        filter_stoped=False,
        filter_failed=False
    )

    def _get_model_key(model_id, model_tag):
        """Generate key for grouping by model+tag"""
        return f"{model_id}__{model_tag}"

    def _get_execution_key(execution_info):
        """Generate unique key for each execution"""
        return execution_info['pipeline_execution_id']

    @lru_cache(maxsize=128)
    def _get_expected_stack_name(model_id, model_tag):
        """Generate expected CloudFormation stack name for a model (cached)"""
        return Model.get_model_stack_name_prefix(model_id, model_tag)

    def _batch_check_stacks_active(stack_names):
        """Batch check if multiple CloudFormation stacks are active (optimized)"""
        if not stack_names:
            return {}

        active_status = {}

        try:
            cf = boto3.client("cloudformation", region_name=get_current_region())

            # Use list_stacks to get all stacks at once (much faster than individual describe_stacks)
            paginator = cf.get_paginator('list_stacks')
            all_stacks = {}

            for page in paginator.paginate():
                for stack in page['StackSummaries']:
                    stack_name = stack['StackName']
                    if stack_name in stack_names:
                        stack_status = stack['StackStatus']

                        # Inactive states (deleted states only)
                        deleted_states = ["DELETE_COMPLETE", "DELETE_IN_PROGRESS"]
                        all_stacks[stack_name] = stack_status not in deleted_states

            # Set results for all requested stacks
            for stack_name in stack_names:
                active_status[stack_name] = all_stacks.get(stack_name, False)

        except Exception as e:
            logger.warning(f"Error batch checking stack status: {e}")
            # Fallback: assume all stacks are inactive
            for stack_name in stack_names:
                active_status[stack_name] = False

        return active_status

    # Performance optimization: Use parallel processing for data fetching
    start_time = time.time()

    def fetch_model_stacks():
        return get_model_stacks()

    def fetch_pipeline_executions():
        return active_executuion_infos

    # Fetch data in parallel (if needed, but pipeline executions are already fetched)
    model_stacks = get_model_stacks()
    logger.debug(f"Fetched {len(model_stacks)} model stacks in {time.time() - start_time:.2f}s")

    # Process model stacks
    model_stacks_by_model = {}
    for model_stack in model_stacks:
        model_key = _get_model_key(model_stack['model_id'], model_stack['model_tag'])

        # For completed stacks, keep only the latest one per model+tag
        if model_key not in model_stacks_by_model:
            model_stacks_by_model[model_key] = model_stack
        else:
            # Keep the more recent one based on creation time
            existing_time = model_stacks_by_model[model_key].get('create_time', '')
            current_time = model_stack.get('create_time', '')
            if current_time > existing_time:
                model_stacks_by_model[model_key] = model_stack

    # Pre-filter executions for basic validation (fast)
    pre_filtered_executions = []
    for execution_info in active_executuion_infos:
        execution_status = execution_info.get('status', '')
        stage_name = execution_info.get('stage_name', '')

        # Skip executions with unknown status or unknown stage
        if (not execution_status or execution_status.lower() == 'unknown' or
            not stage_name or stage_name.lower() == 'unknown'):
            continue

        pre_filtered_executions.append(execution_info)

    logger.debug(f"Pre-filtered {len(pre_filtered_executions)} executions from {len(active_executuion_infos)}")

    # Batch check stack status for succeeded executions only (optimization)
    succeeded_executions = [e for e in pre_filtered_executions if e.get('status') == 'Succeeded']
    stack_names_to_check = []
    execution_to_stack_map = {}

    for execution_info in succeeded_executions:
        # Use expected stack name instead of expensive Deploy stage lookup
        expected_stack_name = _get_expected_stack_name(
            execution_info['model_id'],
            execution_info['model_tag']
        )
        stack_names_to_check.append(expected_stack_name)
        execution_to_stack_map[execution_info['pipeline_execution_id']] = expected_stack_name

    # Batch check all stacks at once (major performance improvement)
    stack_active_status = _batch_check_stacks_active(stack_names_to_check)
    logger.debug(f"Batch checked {len(stack_names_to_check)} stacks in {time.time() - start_time:.2f}s")

    # Filter active executions based on batch results
    validated_active_executions = []
    active_executions_by_model = {}
    active_executions_by_id = {}

    for execution_info in pre_filtered_executions:
        model_key = _get_model_key(execution_info['model_id'], execution_info['model_tag'])
        execution_status = execution_info.get('status', '')

        # Include execution based on optimized logic
        should_include = False

        if execution_status in ['InProgress', 'Stopping']:
            # Always include in-progress executions
            should_include = True
        elif execution_status == 'Succeeded':
            # For successful executions, use batch check results
            expected_stack_name = execution_to_stack_map.get(execution_info['pipeline_execution_id'])
            should_include = stack_active_status.get(expected_stack_name, False)
        elif execution_status in ['Failed', 'Stopped']:
            # Include failed/stopped executions for visibility
            should_include = True

        if should_include:
            validated_active_executions.append(execution_info)

            # Group by model+tag to handle parallel executions
            if model_key not in active_executions_by_model:
                active_executions_by_model[model_key] = []
            active_executions_by_model[model_key].append(execution_info)

            # Also index by execution ID for quick lookup
            exec_key = _get_execution_key(execution_info)
            active_executions_by_id[exec_key] = execution_info

    logger.debug(f"Total status processing time: {time.time() - start_time:.2f}s")

    ret = {
        "inprogress": [],
        "completed": []
    }

    # If specific model requested
    if model_id is not None:
        cur_model_key = _get_model_key(model_id, model_tag)

        # Add ALL parallel executions for this model+tag (already validated)
        if cur_model_key in active_executions_by_model:
            ret['inprogress'].extend(active_executions_by_model[cur_model_key])

        # Add completed stack if exists and no active executions
        if cur_model_key in model_stacks_by_model and not ret['inprogress']:
            ret['completed'].append(model_stacks_by_model[cur_model_key])

        return ret

    # If no specific model requested, return all
    # Add all validated active executions (no deduplication - show all parallel executions)
    for executions in active_executions_by_model.values():
        ret['inprogress'].extend(executions)

    # Add completed stacks (only if no active executions for that model+tag)
    for model_key, stack_info in model_stacks_by_model.items():
        if model_key not in active_executions_by_model:
            ret['completed'].append(stack_info)

    return ret


def get_parallel_executions_for_model(model_id: str, model_tag: str = MODEL_DEFAULT_TAG):
    """
    Get all parallel executions for a specific model+tag combination.
    Useful for monitoring multiple concurrent deployments of the same model.
    """
    check_env_stack_exist_and_complete()
    active_executuion_infos = get_pipeline_active_executions(
        pipeline_name=CODEPIPELINE_NAME,
        filter_stoped=False,
        filter_failed=False
    )

    model_key = f"{model_id}__{model_tag}"
    parallel_executions = []

    for execution_info in active_executuion_infos:
        execution_model_key = f"{execution_info['model_id']}__{execution_info['model_tag']}"
        if execution_model_key == model_key:
            parallel_executions.append(execution_info)

    return parallel_executions


def get_execution_summary():
    """
    Get a summary of all executions grouped by model for better visibility
    in PARALLEL mode.
    """
    check_env_stack_exist_and_complete()
    active_executuion_infos = get_pipeline_active_executions(
        pipeline_name=CODEPIPELINE_NAME,
        filter_stoped=False,
        filter_failed=False
    )

    # Group by model+tag
    executions_by_model = {}
    for execution_info in active_executuion_infos:
        model_key = f"{execution_info['model_id']}__{execution_info['model_tag']}"
        if model_key not in executions_by_model:
            executions_by_model[model_key] = {
                'model_id': execution_info['model_id'],
                'model_tag': execution_info['model_tag'],
                'executions': []
            }
        executions_by_model[model_key]['executions'].append({
            'pipeline_execution_id': execution_info['pipeline_execution_id'],
            'status': execution_info['status'],
            'stage_name': execution_info['stage_name'],
            'instance_type': execution_info['instance_type'],
            'engine_type': execution_info['engine_type'],
            'service_type': execution_info['service_type'],
            'create_time': execution_info['create_time']
        })

    return executions_by_model


def validate_parallel_execution_limit(model_id: str, model_tag: str = MODEL_DEFAULT_TAG) -> tuple[bool, str]:
    """
    Validate that we don't exceed reasonable limits for parallel executions
    of the same model to prevent resource exhaustion.
    """
    parallel_executions = get_parallel_executions_for_model(model_id, model_tag)
    current_count = len(parallel_executions)

    if current_count >= MAX_PARALLEL_EXECUTIONS_PER_MODEL:
        return False, f"Maximum parallel executions ({MAX_PARALLEL_EXECUTIONS_PER_MODEL}) reached for model {model_id} (tag: {model_tag}). Current: {current_count}"

    return True, f"Parallel execution allowed. Current count: {current_count}/{MAX_PARALLEL_EXECUTIONS_PER_MODEL}"
