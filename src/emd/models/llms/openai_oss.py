from ..engines import vllm_gptoss_engine
from .. import Model
from ..frameworks import fastapi_framework
from ..services import (
    sagemaker_service,
    sagemaker_async_service,
    ecs_service,
    local_service
)
from emd.models.utils.constants import ModelType
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
from ..model_series import GPTOSS_SERIES
Model.register(
    dict(
        model_id = "gpt-oss-20b",
        supported_engines=[vllm_gptoss_engine],
        supported_instances=[
            g5d2xlarge_instance,
            g5d4xlarge_instance,
            g5d8xlarge_instance,
            g5d16xlarge_instance,
            # g5d24xlarge_instance,
            # g5d48xlarge_instance,
            local_instance
        ],
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
        huggingface_model_id="openai/gpt-oss-20b",
        modelscope_model_id="openai/gpt-oss-20b",
        require_huggingface_token=False,
        application_scenario="Agent, tool use, translation, summary",
        description="GPT-OSS (GPT Open Source Software) is OpenAI's initiative to provide open-source AI models, making advanced language models accessible to developers, researchers, and organizations. These models are designed for building, experimenting, and scaling generative AI applications while fostering innovation and collaboration in the open-source AI community.",
        model_type=ModelType.LLM,
        model_series=GPTOSS_SERIES
    )
)


Model.register(
    dict(
        model_id = "gpt-oss-120b",
        supported_engines=[vllm_gptoss_engine],
        supported_instances=[
            g5d12xlarge_instance,
            g5d24xlarge_instance,
            g5d48xlarge_instance,
            local_instance
        ],
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
        huggingface_model_id="openai/gpt-oss-120b",
        modelscope_model_id="openai/gpt-oss-120b",
        require_huggingface_token=False,
        application_scenario="Agent, tool use, translation, summary",
        description="GPT-OSS (GPT Open Source Software) is OpenAI's initiative to provide open-source AI models, making advanced language models accessible to developers, researchers, and organizations. These models are designed for building, experimenting, and scaling generative AI applications while fostering innovation and collaboration in the open-source AI community.",
        model_type=ModelType.LLM,
        model_series=GPTOSS_SERIES
    )
)
