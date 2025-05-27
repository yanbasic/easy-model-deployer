from .model import (
    Engine,
    # MultiModelEngine,
    Framework,
    Model,
    ModelSeries,
    Service,
    Instance,
    ExecutableConfig,
    ValueWithDefault
)



from . import (
    llms,
    vlms,
    comfyui,
    asr,
    embeddings,
    reranks,
    custom,
)
# text-2-image,text-2-video

from . import engines
from . import instances
from . import services
from . import model_series
from . import frameworks

# Model.register_from_json_file(
#     "src/emd/models/custom_model.json"
# )