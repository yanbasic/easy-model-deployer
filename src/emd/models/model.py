import os
import re
import json
import importlib
from pydantic import BaseModel,Field,ConfigDict,SerializeAsAny
from typing import List,ClassVar,Union,TypeVar, Generic,Any,Dict
from .utils.constants import (
    EngineType,
    InstanceType,
    ServiceType,
    FrameworkType,
    ModelType,
    ModelSeriesType,
    ModelFilesDownloadSource
    # ModelPrepareMethod
)
import boto3
from .utils.text_utilities import normalize
from emd.constants import (
    MODEL_STACK_NAME_PREFIX,
    MODEL_DEFAULT_TAG
)

from emd.revision import convert_stack_name_to_version_name

T = TypeVar('T', bound='Model')


abs_dir = os.path.dirname(__file__)

class ModelBase(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        extra = "allow",
        use_enum_values = True
    )

class ValueWithDefault(BaseModel):
    name: str
    default: Any

class Instance(ModelBase):
    instance_type: InstanceType
    gpu_num: Union[int,None] = Field(description="Gpu num of NVIDIA chips",default=None)
    neuron_core_num: Union[int,None] = Field(description="NeuronCore num of Inferentia2 chips",default=None)
    description: str
    vcpu: int
    memory: int = Field(description="memory of the instance, use `GiB` unit")
    support_cn_region: bool = False

    gib_to_mb: ClassVar[int] = 1073
    vcpu_to_cpu: ClassVar[int] = 1024
    instance_map: ClassVar[dict] = {}
    def model_post_init(self, __context: Any) -> None:
        Instance.instance_map[self.instance_type] = self

    @classmethod
    def get_ecs_container_memory(cls,instance_type:InstanceType):
        instance = Instance.instance_map[instance_type]
        return f"{int(instance.memory * 1024/cls.gib_to_mb)*1024}"

    @classmethod
    def get_ecs_container_cpu(cls,instance_type:InstanceType):
        instance = Instance.instance_map[instance_type]
        return f"{min(instance.vcpu,10) * cls.vcpu_to_cpu}"

    @classmethod
    def get_instance_from_instance_type(cls,instance_type:InstanceType):
        return Instance.instance_map[instance_type]

    @classmethod
    def check_inf2_instance(cls,instance_type:str):
        return "inf2" in instance_type

class Engine(ModelBase):
    engine_type: EngineType
    engine_dockerfile_config: Union[dict,None] = Field(default_factory=dict)
    engine_cls: Union[str,None] = None
    dockerfile_name: str = "Dockerfile"
    base_image_account_id: Union[str,None] = None
    base_image_host: Union[str,None] = None
    use_public_ecr: bool = False
    docker_login_region: Union[str,None] = None
    python_name: str = "python3"

    # this field is used to modify the model fields like qwen2 yarn config
    model_files_modify_hook: Union[str,None] = None
    model_files_modify_hook_kwargs: Union[dict,None] = None
    description:str = ""
    support_inf2_instance: bool = False


    @staticmethod
    def load_model_files_modify_hook(hook_path:str):
        *module_path,hook_name = hook_path.split(".")
        module = importlib.import_module(".".join(module_path))
        return getattr(module,hook_name)


class MultiModelEngine(ModelBase):
    engines: Dict[str,Engine]


class Service(ModelBase):
    cfn_parameters:dict = Field(default_factory=dict)
    service_type: ServiceType
    name: str
    description: str
    support_cn_region: bool
    need_vpc: bool = False

    # class vars
    service_name_maps: ClassVar[dict] = {}
    service_type_maps: ClassVar[dict] = {}

    def model_post_init(self, __context: Any) -> None:
        Service.service_name_maps[self.name] = self
        Service.service_type_maps[self.service_type] = self


    @classmethod
    def get_service_from_service_type(cls, service_type:ServiceType):
        return cls.service_type_maps[service_type]

    @classmethod
    def get_service_from_name(cls, name:str):
        return cls.service_name_maps[name]

    # # TODO
    # def get_quota_args(self,instance_type:InstanceType):
    #     raise NotImplementedError



class Framework(ModelBase):
    framework_type: FrameworkType
    description: str



class ExecutableConfig(ModelBase):
    region: Union[str,None] = None
    current_engine: Union[Engine,None] = None
    current_instance: Union[Instance,None] = None
    current_service: Union[Service,None] = None
    current_framework: Union[Framework,None] = None
    extra_params: Union[dict,None] = None
    model_s3_bucket: Union[str,None] = None
    model_tag: str = MODEL_DEFAULT_TAG


class ModelSeries(ModelBase):
    model_series_name:ModelSeriesType
    description: str =  ""
    reference_link: str = ""
    # class vars
    model_series_name_maps: ClassVar[dict] = {}

    def model_post_init(self, __context: Any) -> None:
        ModelSeries.model_series_name_maps[self.model_series_name] = self

    @classmethod
    def get_model_series_from_name(cls, model_series_name:ModelSeriesType):
        return cls.model_series_name_maps[model_series_name]

class Model(ModelBase,Generic[T]):
    model_map: ClassVar[dict] = {}
    model_id: str = Field(description="model id")
    supported_engines: List[SerializeAsAny[Engine]] = Field(description="supported engine")
    supported_instances: List[SerializeAsAny[Instance]] = Field(description="supported instances")
    supported_services: List[SerializeAsAny[Service]] = Field(description="supported services")
    supported_frameworks: List[SerializeAsAny[Framework]] = Field(description="supported frameworks")
    allow_china_region: bool = False

    # allow_china_region_ecs: bool = False
    huggingface_model_id: str = ""
    huggingface_endpoints: List[str] = ["https://huggingface.co","https://hf-mirror.com"]
    disable_hf_transfer:bool = True

    huggingface_model_download_kwargs: dict = Field(default_factory=dict)
    ollama_model_id:Union[str,None] = None
    require_huggingface_token: bool = False
    modelscope_model_id: str = ""
    require_modelscope_token: bool = False
    application_scenario: str = ""
    description: str =  ""
    model_type: ModelType = ModelType.LLM
    need_prepare_model: bool = True
    # download model files directly from s3
    model_files_s3_path: Union[str,None] = None
    model_files_local_path: Union[str,None] = None
    model_files_download_source: ModelFilesDownloadSource = ModelFilesDownloadSource.AUTO
    model_series: ModelSeries = None
    executable_config: Union[ExecutableConfig,None] = None

    @classmethod
    def register(cls, model_dict) -> T:
        model = cls(**model_dict)
        Model.model_map[model.model_id] = model
        return model

    @classmethod
    def register_from_json_str(cls, json_str) -> T:
        def get_all_engines():
            from . import engines
            # get all engine names
            engine_list = [(i, getattr(engines,i)) for i in dir(engines) if isinstance(getattr(engines,i),Engine)]
            engine_dict = {}
            for engine_name, engine in engine_list:
                if engine_name in engine_dict:
                    raise ValueError(f"engine_type:{engine.engine_type} is duplicated")
                engine_dict[engine_name] = engine
            return engine_dict
        def get_all_instances():
            from . import instances
            # get all instance names
            instance_list = [(i, getattr(instances,i)) for i in dir(instances) if isinstance(getattr(instances,i),Instance)]
            instance_dict = {}
            for instance_name, instance in instance_list:
                if instance_name in instance_dict:
                    raise ValueError(f"instance_type:{instance.instance_type} is duplicated")
                instance_dict[instance_name] = instance
            return instance_dict
        def get_all_services():
            from . import services
            # get all service names
            service_list = [(i, getattr(services,i)) for i in dir(services) if isinstance(getattr(services,i),Service)]
            service_dict = {}
            for service_name, service in service_list:
                if service_name in service_dict:
                    raise ValueError(f"service_type:{service.service_type} is duplicated")
                service_dict[service_name] = service
            return service_dict
        def get_all_frameworks():
            from . import frameworks
            # get all framework names
            framework_list = [(i, getattr(frameworks,i)) for i in dir(frameworks) if isinstance(getattr(frameworks,i),Framework)]
            framework_dict = {}
            for framework_name, framework in framework_list:
                if framework_name in framework_dict:
                    raise ValueError(f"framework_type:{framework.framework_type} is duplicated")
                framework_dict[framework_name] = framework
            return framework_dict
        def format_custom_model_dict(custom_model_dict:dict):
            new_custom_model_dict = custom_model_dict.copy()
            engine_dict = get_all_engines()
            for engine in custom_model_dict.get("supported_engines",[]):
                if engine not in engine_dict:
                    raise ValueError(f"engine_type:{engine} is not supported")
            new_custom_model_dict["supported_engines"] = [engine_dict[i] for i in custom_model_dict.get("supported_engines",[])]
            instance_dict = get_all_instances()
            for instance in custom_model_dict.get("supported_instances",[]):
                if instance not in instance_dict:
                    raise ValueError(f"instance_type:{instance} is not supported")
            new_custom_model_dict["supported_instances"] = [instance_dict[i] for i in custom_model_dict.get("supported_instances",[])]
            service_dict = get_all_services()
            for service in custom_model_dict.get("supported_services",[]):
                if service not in service_dict:
                    raise ValueError(f"service_type:{service} is not supported")
            new_custom_model_dict["supported_services"] = [service_dict[i] for i in custom_model_dict.get("supported_services",[])]
            framework_dict = get_all_frameworks()
            for framework in custom_model_dict.get("supported_frameworks",[]):
                if framework not in framework_dict:
                    raise ValueError(f"framework_type:{framework} is not supported")
            new_custom_model_dict["supported_frameworks"] = [framework_dict[i] for i in custom_model_dict.get("supported_frameworks",[])]
            print(new_custom_model_dict)
            return new_custom_model_dict
        model_dict = json.loads(json_str)
        model_dict = format_custom_model_dict(model_dict)
        model = cls(**model_dict)
        Model.model_map[model.model_id] = model
        return model

    @classmethod
    def register_from_json_file(cls, json_file_path) -> T:
        with open(json_file_path, "r") as f:
            model_dict_str = f.read()
        return cls.register_from_json_str(model_dict_str)

    @classmethod
    def get_model(cls ,model_id:str,update:dict = None) -> T:
        try:
            model = cls.model_map[model_id]
        except KeyError:
            raise KeyError(f"model_id:{model_id} is not supported")
        if update:
            model = model.copy(update=update)
        return model

    @classmethod
    def get_supported_models(cls,detail=False) -> dict:
        if not detail:
            return {model_id: model.model_type for model_id,model in cls.model_map.items()}
        return {model_id: model.model_dump() for model_id,model in cls.model_map.items()}

    def find_current_engine(self,engine_type:str) -> dict:
        supported_engines:List[Engine]  = self.supported_engines
        cur_engine = None
        for supported_engine in supported_engines:
            if supported_engine.engine_type == engine_type:
                cur_engine = supported_engine.model_dump()
                break
        assert cur_engine is not None, (engine_type,supported_engines)
        return cur_engine

    def find_current_instance(self,instance_type):
        supported_instances = self.supported_instances
        cur_instance = None
        for supported_instance in supported_instances:
            if supported_instance.instance_type == instance_type:
                cur_instance = supported_instance.model_dump()
                break
        assert cur_instance is not None, (instance_type, supported_instances)
        return cur_instance

    def find_current_service(self,service_type):
        supported_services = self.supported_services
        cur_service = None
        for supported_service in supported_services:
            if supported_service.service_type == service_type:
                cur_service = supported_service.model_dump()
                break
        assert cur_service is not None, (service_type, supported_services)

        return cur_service

    def find_current_framework(self,framework_type):
        supported_frameworks = self.supported_frameworks
        cur_framework = None
        for supported_framework in supported_frameworks:
            if supported_framework.framework_type == framework_type:
                cur_framework = supported_framework.model_dump()
                break
        assert cur_framework is not None, (framework_type, supported_frameworks)
        return cur_framework


    @property
    def supported_instance_types(self):
        return [i.instance_type for i in self.supported_instances]

    @property
    def supported_service_types(self):
        return [i.service_type for i in self.supported_services]

    @property
    def supported_engine_types(self):
        return [i.engine_type for i in self.supported_engines]

    @property
    def supported_framework_types(self):
        return [i.framework_type for i in self.supported_frameworks]


    def get_engine(self) -> Engine:
        assert self.executable_config.current_engine is not None, self.executable_config.current_engine
        engine_cls_path = self.executable_config.current_engine.engine_cls
        *engine_cls_path,cls_name = engine_cls_path.split(".")
        module = importlib.import_module("backend." + ".".join(engine_cls_path))
        return getattr(module,cls_name)(self)

    def get_engine_dir(self) -> str:
        *engine_cls_path,_,_ = self.executable_config.current_engine.engine_cls.split(".")
        return os.path.join("backend","/".join(engine_cls_path))

    def get_dockerfile(self) -> str:
        engine_dir = self.get_engine_dir()
        dockerfile_abs_path = os.path.join(
            engine_dir,
            self.executable_config.current_engine.dockerfile_name
        )
        return dockerfile_abs_path

    def convert_to_execute_model(
            self,
            engine_type,
            instance_type,
            service_type,
            framework_type,
            extra_params,
            model_tag=MODEL_DEFAULT_TAG,
            region=None,
            model_s3_bucket=None
            # executable_config:ExecutableConfig,
            # **model_params
        ) -> T:
        engine_params = extra_params.get("engine_params", {})
        model_params = extra_params.get("model_params", {})
        service_params = extra_params.get("service_params",{})
        framework_params = extra_params.get("framework_params",{})
        instance_params = extra_params.get("instance_params",{})

        current_engine = self.find_current_engine(engine_type)
        current_engine.update(engine_params)

        current_instance = self.find_current_instance(instance_type)
        current_instance.update(instance_params)


        current_service = self.find_current_service(service_type)
        current_service.update(service_params)


        current_framework = self.find_current_framework(framework_type)
        current_framework.update(framework_params)


        executable_config = ExecutableConfig(
            region=region,
            current_engine=current_engine,
            current_instance=current_instance,
            current_service=current_service,
            current_framework=current_framework,
            model_s3_bucket=model_s3_bucket,
            extra_params=extra_params,
            model_tag=model_tag
        )

        model = self.model_copy(update={
            "executable_config":executable_config,
            **model_params
        })
        return model



    def get_execute_dir(self) -> str:
        if self.executable_config.model_tag == MODEL_DEFAULT_TAG:
            return f"deploy_artifacts/{self.model_id}_artifacts"
        else:
            return f"deploy_artifacts/{self.model_id}_{self.executable_config.model_tag}_artifacts"


    def get_normalized_model_id(self):
        return self.normalize_model_id(self.model_id)

    @classmethod
    def normalize_model_id(cls,model_id):
        return normalize(model_id).lower()

    @classmethod
    def get_model_stack_name_prefix(cls,model_id,model_tag=MODEL_DEFAULT_TAG):
        model_id_with_tag = model_id
        if model_tag and model_tag != MODEL_DEFAULT_TAG:
            model_id_with_tag = f"{model_id_with_tag}-{model_tag}"
        return f"{MODEL_STACK_NAME_PREFIX}-{cls.normalize_model_id(model_id_with_tag)}"

    @classmethod
    def get_deploy_version_from_stack_name(cls,stack_name):
        try:
            m_deploy_version = re.match(MODEL_STACK_NAME_PREFIX+"-(\d+-\d+-\d+)-",stack_name)
            return convert_stack_name_to_version_name(m_deploy_version.group(1))
        except Exception as e:
            raise ValueError(f"stack_name:{stack_name} is not a valid model stack name")

    def get_image_build_account_id(self):
        current_account_id = boto3.client("sts").get_caller_identity()["Account"]
        build_image_account_id = (
            self.executable_config.current_engine.base_image_account_id or \
            current_account_id
        )
        return build_image_account_id

    def get_image_push_account_id(self):
        current_account_id = boto3.client("sts").get_caller_identity()["Account"]
        return current_account_id

    def get_image_uri(
        sef,
        account_id,
        region,
        image_name,
        image_tag
    ):
        if "cn" in region:
            image_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com.cn/{image_name}:{image_tag}"
        else:
            image_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{image_name}:{image_tag}"
        return image_uri

    def get_image_host(self,image_uri):
        return image_uri.split("/")[0]
