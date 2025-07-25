import boto3
from typing import Dict, List, Optional, Tuple
import concurrent.futures
import time
from functools import lru_cache

from emd.constants import CODEPIPELINE_NAME, MODEL_DEFAULT_TAG
from emd.utils.aws_service_utils import (
    check_stack_status,
    get_pipeline_active_executions,
    get_model_stacks,
    check_env_stack_exist_and_complete,
    get_current_region
)
from emd.utils.logger_utils import get_logger

# Constants
PARALLEL_EXECUTION_SEPARATOR = "__"
MAX_PARALLEL_EXECUTIONS_PER_MODEL = 5
PARALLEL_API_TIMEOUT = 30  # seconds

logger = get_logger(__name__)


class StatusError(Exception):
    """Base exception for status-related errors"""
    pass


class PipelineStatusError(StatusError):
    """Exception raised when pipeline status cannot be retrieved"""
    pass


class StackStatusError(StatusError):
    """Exception raised when stack status cannot be retrieved"""
    pass


def get_pipeline_execution_status(
    pipeline_execution_id: str,
    pipeline_name: str = CODEPIPELINE_NAME,
    region: Optional[str] = None
) -> Dict:
    """
    Get detailed status information for a specific pipeline execution.
    
    Args:
        pipeline_execution_id: The unique identifier for the pipeline execution
        pipeline_name: Name of the CodePipeline (defaults to CODEPIPELINE_NAME)
        region: AWS region (defaults to current region)
    
    Returns:
        Dict containing execution status, stage information, and metadata
        
    Raises:
        PipelineStatusError: If pipeline execution cannot be found or accessed
    """
    if region is None:
        region = get_current_region()

    try:
        client = boto3.client('codepipeline', region_name=region)
        
        response = client.get_pipeline_execution(
            pipelineName=pipeline_name,
            pipelineExecutionId=pipeline_execution_id
        )
        
        execution = response['pipelineExecution']
        status = execution['status']
        status_summary = execution.get('statusSummary', "")

        result = {
            "status": status,
            "status_code": 1 if status not in ['Stopped', 'Succeeded', 'Cancelled', "Failed"] else 0,
            "is_succeeded": status == 'Succeeded',
            "stage_name": None,
            "status_summary": status_summary,
            "pipeline_execution_id": pipeline_execution_id
        }

        # Get current stage information
        try:
            active_executions = get_pipeline_active_executions(
                pipeline_name=pipeline_name,
                client=client,
                return_dict=True,
                filter_stoped=False,
                filter_failed=False
            )

            if pipeline_execution_id in active_executions:
                execution_info = active_executions[pipeline_execution_id]
                result.update({
                    'stage_name': execution_info['stage_name'],
                    'model_id': execution_info['model_id'],
                    'model_tag': execution_info['model_tag'],
                    'instance_type': execution_info['instance_type'],
                    'engine_type': execution_info['engine_type'],
                    'service_type': execution_info['service_type']
                })

        except Exception as e:
            logger.warning(f"Could not get stage info for execution {pipeline_execution_id}: {e}")
            result['stage_name'] = f"Error getting stage info: {str(e)}"

        return result
        
    except client.exceptions.PipelineExecutionNotFoundException:
        return {
            "status": "NotFound",
            "status_code": 0,
            "is_succeeded": False,
            "stage_name": None,
            "status_summary": "Pipeline execution not found",
            "pipeline_execution_id": pipeline_execution_id
        }
    except Exception as e:
        logger.error(f"Error getting pipeline execution status: {e}")
        raise PipelineStatusError(f"Failed to get pipeline execution status: {e}")


def get_destroy_status(stack_name: str) -> Dict:
    """
    Get the destruction status of a CloudFormation stack.
    
    Args:
        stack_name: Name of the CloudFormation stack
        
    Returns:
        Dict containing destruction status and success indicator
        
    Raises:
        StackStatusError: If stack status cannot be determined
    """
    try:
        stack_status = check_stack_status(stack_name)
        status = stack_status.status
        
        if not stack_status.is_exist:
            return {
                "status_code": 0,
                "status": status,
                "is_succeeded": True
            }
            
        if status == "DELETE_FAILED":
            return {
                "status_code": 0,
                "is_succeeded": False,
                "status": status,
            }
            
        return {
            "status_code": 1,
            "is_succeeded": False,
            "status": status,
        }
        
    except Exception as e:
        logger.error(f"Error getting destroy status for stack {stack_name}: {e}")
        raise StackStatusError(f"Failed to get destroy status: {e}")


def get_model_status(model_id: Optional[str] = None, model_tag: str = MODEL_DEFAULT_TAG) -> Dict:
    """
    Get comprehensive status of model deployments with optimal performance.
    
    This function provides real-time status information for model deployments by:
    1. Fetching pipeline executions and CloudFormation stacks in parallel
    2. Filtering out invalid executions (Failed with Unknown stage)
    3. Organizing results by in-progress and completed deployments
    
    Args:
        model_id: Specific model ID to filter by. If None, returns all models
        model_tag: Model tag to filter by
        
    Returns:
        Dict with 'inprogress' and 'completed' keys containing model information:
        - 'inprogress': List of active pipeline executions
        - 'completed': List of completed CloudFormation stacks
        
    Raises:
        StatusError: If status information cannot be retrieved
    """
    try:
        check_env_stack_exist_and_complete()
        
        start_time = time.time()
        
        # Parallel data fetching for optimal performance
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both AWS API calls simultaneously
            pipeline_future = executor.submit(
                get_pipeline_active_executions,
                pipeline_name=CODEPIPELINE_NAME,
                filter_stoped=False,
                filter_failed=False
            )
            stacks_future = executor.submit(get_model_stacks)
            
            # Wait for both results with timeout
            try:
                active_executions = pipeline_future.result(timeout=PARALLEL_API_TIMEOUT)
                model_stacks = stacks_future.result(timeout=PARALLEL_API_TIMEOUT)
            except concurrent.futures.TimeoutError:
                logger.error("Timeout waiting for AWS API responses")
                raise StatusError("Timeout retrieving status information")
        
        logger.debug(f"Parallel data fetch completed in {time.time() - start_time:.2f}s")
        
        # Filter out invalid executions
        filtered_executions = _filter_valid_executions(active_executions)
        
        # Organize results
        result = {
            "inprogress": [],
            "completed": []
        }
        
        if model_id is not None:
            # Filter for specific model
            result['inprogress'] = _filter_executions_by_model(
                filtered_executions, model_id, model_tag
            )
            result['completed'] = _filter_stacks_by_model(
                model_stacks, model_id, model_tag
            )
        else:
            # Return all models
            result['inprogress'] = filtered_executions
            result['completed'] = model_stacks
        
        logger.debug(f"Total status processing time: {time.time() - start_time:.2f}s")
        return result
        
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise StatusError(f"Failed to get model status: {e}")


def get_parallel_executions_for_model(
    model_id: str, 
    model_tag: str = MODEL_DEFAULT_TAG
) -> List[Dict]:
    """
    Get all parallel executions for a specific model+tag combination.
    
    Useful for monitoring multiple concurrent deployments of the same model.
    
    Args:
        model_id: The model identifier
        model_tag: The model tag
        
    Returns:
        List of execution information dictionaries
        
    Raises:
        StatusError: If execution information cannot be retrieved
    """
    try:
        check_env_stack_exist_and_complete()
        
        start_time = time.time()
        
        # Optimized single API call
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            pipeline_future = executor.submit(
                get_pipeline_active_executions,
                pipeline_name=CODEPIPELINE_NAME,
                filter_stoped=False,
                filter_failed=False
            )
            active_executions = pipeline_future.result(timeout=PARALLEL_API_TIMEOUT)
        
        logger.debug(f"Pipeline data fetch completed in {time.time() - start_time:.2f}s")

        # Filter for specific model
        model_key = f"{model_id}__{model_tag}"
        parallel_executions = []

        for execution_info in active_executions:
            execution_model_key = f"{execution_info['model_id']}__{execution_info['model_tag']}"
            if execution_model_key == model_key:
                parallel_executions.append(execution_info)

        return parallel_executions
        
    except Exception as e:
        logger.error(f"Error getting parallel executions for model {model_id}: {e}")
        raise StatusError(f"Failed to get parallel executions: {e}")


def get_execution_summary() -> Dict:
    """
    Get a summary of all executions grouped by model.
    
    Provides a comprehensive view of all model deployments organized by model+tag
    for better visibility in parallel deployment scenarios.
    
    Returns:
        Dict with model keys containing execution summaries
        
    Raises:
        StatusError: If execution summary cannot be generated
    """
    try:
        check_env_stack_exist_and_complete()
        
        start_time = time.time()
        
        # Optimized single API call
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            pipeline_future = executor.submit(
                get_pipeline_active_executions,
                pipeline_name=CODEPIPELINE_NAME,
                filter_stoped=False,
                filter_failed=False
            )
            active_executions = pipeline_future.result(timeout=PARALLEL_API_TIMEOUT)
        
        logger.debug(f"Pipeline data fetch completed in {time.time() - start_time:.2f}s")

        # Group executions by model+tag
        executions_by_model = {}
        for execution_info in active_executions:
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
        
    except Exception as e:
        logger.error(f"Error getting execution summary: {e}")
        raise StatusError(f"Failed to get execution summary: {e}")


def validate_parallel_execution_limit(
    model_id: str, 
    model_tag: str = MODEL_DEFAULT_TAG
) -> Tuple[bool, str]:
    """
    Validate that parallel execution limits are not exceeded.
    
    Prevents resource exhaustion by enforcing reasonable limits on
    concurrent deployments of the same model.
    
    Args:
        model_id: The model identifier
        model_tag: The model tag
        
    Returns:
        Tuple of (is_valid, message) indicating if deployment is allowed
        
    Raises:
        StatusError: If validation cannot be performed
    """
    try:
        parallel_executions = get_parallel_executions_for_model(model_id, model_tag)
        current_count = len(parallel_executions)

        if current_count >= MAX_PARALLEL_EXECUTIONS_PER_MODEL:
            return False, (
                f"Maximum parallel executions ({MAX_PARALLEL_EXECUTIONS_PER_MODEL}) "
                f"reached for model {model_id} (tag: {model_tag}). "
                f"Current: {current_count}"
            )

        return True, (
            f"Parallel execution allowed. "
            f"Current count: {current_count}/{MAX_PARALLEL_EXECUTIONS_PER_MODEL}"
        )
        
    except Exception as e:
        logger.error(f"Error validating parallel execution limit: {e}")
        raise StatusError(f"Failed to validate execution limit: {e}")


# Private helper functions

def _filter_valid_executions(executions: List[Dict]) -> List[Dict]:
    """Filter out invalid executions (Failed with Unknown stage)"""
    filtered_executions = []
    
    for execution_info in executions:
        execution_status = execution_info.get('status', '')
        stage_name = execution_info.get('stage_name', '')
        
        # Skip executions with 'Failed (Unknown)' status
        if execution_status == 'Failed' and stage_name == 'Unknown':
            continue
            
        filtered_executions.append(execution_info)
    
    return filtered_executions


def _filter_executions_by_model(
    executions: List[Dict], 
    model_id: str, 
    model_tag: str
) -> List[Dict]:
    """Filter executions for a specific model+tag combination"""
    filtered_executions = []
    
    for execution_info in executions:
        if (execution_info['model_id'] == model_id and
            execution_info['model_tag'] == model_tag):
            filtered_executions.append(execution_info)
    
    return filtered_executions


def _filter_stacks_by_model(
    stacks: List[Dict], 
    model_id: str, 
    model_tag: str
) -> List[Dict]:
    """Filter stacks for a specific model+tag combination"""
    filtered_stacks = []
    
    for stack_info in stacks:
        if (stack_info['model_id'] == model_id and
            stack_info['model_tag'] == model_tag):
            filtered_stacks.append(stack_info)
    
    return filtered_stacks
