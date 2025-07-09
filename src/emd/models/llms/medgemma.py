from ..engines import vllm_medgemma082
from .. import Model
from ..frameworks import fastapi_framework
from ..services import (
    sagemaker_service,
    sagemaker_async_service,
    ecs_service,
    local_service
)
from emd.models.utils.constants import ModelType
from ..model_series import MEDGEMMA_SERIES
from ..instances import (
    g5d2xlarge_instance,
    g5d4xlarge_instance,
    g5d8xlarge_instance,
    g5d12xlarge_instance,
    g5d16xlarge_instance,
    g5d24xlarge_instance,
    g5d48xlarge_instance,
    g6e2xlarge_instance,
    local_instance
)
from ..utils.constants import ModelFilesDownloadSource


Model.register(
    dict(
        model_id = "medgemma-27b-text-it",
        supported_engines=[vllm_medgemma082],
        supported_instances=[
            g5d12xlarge_instance,
            g5d24xlarge_instance,
            g5d48xlarge_instance,
            g5d2xlarge_instance,
            g5d4xlarge_instance,
            g5d8xlarge_instance,
            g5d16xlarge_instance,
            local_instance
        ],
        disable_hf_transfer=True,
        supported_services=[
            sagemaker_service,
            sagemaker_async_service,
            ecs_service,
            local_service
        ],
        supported_frameworks=[
            fastapi_framework
        ],
        allow_china_region=True,
        huggingface_model_id="google/medgemma-27b-text-it",
        modelscope_model_id="google/medgemma-27b-text-it",
        model_files_download_source=ModelFilesDownloadSource.MODELSCOPE,
        # require_huggingface_token=True,
        application_scenario="llm for medical text and image comprehension",
        description="The latest series of medgemma",
        model_type=ModelType.LLM,
        model_series=MEDGEMMA_SERIES,
    )
)


Model.register(
    dict(
        model_id = "medgemma-4b-it",
        supported_engines=[vllm_medgemma082],
        supported_instances=[
            g5d12xlarge_instance,
            g5d24xlarge_instance,
            g5d48xlarge_instance,
            local_instance
        ],
        disable_hf_transfer=True,
        supported_services=[
            sagemaker_service,
            sagemaker_async_service,
            ecs_service,
            local_service
        ],
        supported_frameworks=[
            fastapi_framework
        ],
        allow_china_region=True,
        huggingface_model_id="google/medgemma-4b-it",
        modelscope_model_id="google/medgemma-4b-it",
        model_files_download_source=ModelFilesDownloadSource.MODELSCOPE,
        # require_huggingface_token=True,
        application_scenario="llm for medical text and image comprehension",
        description="The latest series of medgemma",
        model_type=ModelType.LLM,
        model_series=MEDGEMMA_SERIES,
    )
)
