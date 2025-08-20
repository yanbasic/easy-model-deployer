from .. import Model
from ..engines import vllm_higgs_audio_engine091
from ..model_series import HIGGS_AUDIO_SERIES
from ..instances import (
    g5d48xlarge_instance,
    local_instance
)
from ..services import (
    sagemaker_service,
    sagemaker_async_service,
    ecs_service,
    local_service
)
from ..frameworks import fastapi_framework
from emd.models.utils.constants import ModelType

Model.register(
    dict(
        model_id="bosonai-higgs-audio-v2-generation-3B-base",
        model_type=ModelType.AUDIO,
        description="Higgs Audio v2 Generation 3B Base is a powerful multimodal audio generation model that supports voice cloning, smart voice generation, and multi-speaker synthesis. Built on vLLM engine with OpenAI-compatible API for text-to-speech and audio generation tasks.",
        application_scenario="voice cloning, text-to-speech, audio generation, multi-speaker synthesis, smart voice generation",
        supported_engines=[vllm_higgs_audio_engine091],
        supported_instances=[
            g5d48xlarge_instance, local_instance
        ],
        supported_services=[
            sagemaker_service, local_service
        ],
        supported_frameworks=[
            fastapi_framework
        ],
        allow_china_region=True,
        huggingface_model_id="bosonai/higgs-audio-v2-generation-3B-base",
        require_huggingface_token=False,
        need_prepare_model=False,
    )
)
