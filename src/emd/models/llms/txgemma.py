from ..engines import vllm_texgemma082
from .. import Model
from ..frameworks import fastapi_framework
from ..services import (
    sagemaker_service,
    sagemaker_async_service,
    ecs_service,
    local_service
)
from emd.models.utils.constants import ModelType
from ..model_series import TXGEMMA_SERIES
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
        model_id = "txgemma-9b-chat",
        supported_engines=[vllm_texgemma082],
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
        huggingface_model_id="google/txgemma-9b-chat",
        modelscope_model_id="AI-ModelScope/txgemma-9b-chat",
        model_files_download_source=ModelFilesDownloadSource.MODELSCOPE,
        # require_huggingface_token=True,
        application_scenario="llms for the development of therapeutics.",
        description="The latest series of txgemma",
        model_type=ModelType.LLM,
        model_series=TXGEMMA_SERIES,
    )
)


Model.register(
    dict(
        model_id = "txgemma-27b-chat",
        supported_engines=[vllm_texgemma082],
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
        huggingface_model_id="google/txgemma-27b-chat",
        modelscope_model_id="AI-ModelScope/txgemma-27b-chat",
        model_files_download_source=ModelFilesDownloadSource.MODELSCOPE,
        # require_huggingface_token=True,
        application_scenario="llms for the development of therapeutics.",
        description="The latest series of txgemma",
        model_type=ModelType.LLM,
        model_series=TXGEMMA_SERIES,
    )
)
