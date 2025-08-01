#!/usr/bin/env python3
"""
EMD Model Configuration Generator
Extracts model definitions from Python source and generates JavaScript config file
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add EMD source to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / 'src'))

def extract_models():
    """Extract all registered models with their configurations"""
    try:
        from emd.models import Model
        
        models = {}
        for model_id, model in Model.model_map.items():
            try:
                # Extract model series information
                model_series = None
                if hasattr(model, 'model_series') and model.model_series:
                    model_series = {
                        "name": getattr(model.model_series.model_series_name, 'value', str(model.model_series.model_series_name)) if hasattr(model.model_series, 'model_series_name') else '',
                        "description": getattr(model.model_series, 'description', ''),
                        "reference_link": getattr(model.model_series, 'reference_link', '')
                    }
                
                models[model_id] = {
                    "model_id": model.model_id,
                    "model_type": getattr(model.model_type, 'value', str(model.model_type)) if hasattr(model, 'model_type') else 'unknown',
                    "description": getattr(model, 'description', ''),
                    "application_scenario": getattr(model, 'application_scenario', ''),
                    "supported_instances": [
                        getattr(inst.instance_type, 'value', str(inst.instance_type)) if hasattr(inst, 'instance_type') else str(inst)
                        for inst in getattr(model, 'supported_instances', [])
                    ],
                    "supported_engines": [
                        getattr(eng.engine_type, 'value', str(eng.engine_type)) if hasattr(eng, 'engine_type') else str(eng)
                        for eng in getattr(model, 'supported_engines', [])
                    ],
                    "supported_services": [
                        getattr(svc.service_type, 'value', str(svc.service_type)) if hasattr(svc, 'service_type') else str(svc)
                        for svc in getattr(model, 'supported_services', [])
                    ],
                    "allow_china_region": getattr(model, 'allow_china_region', False),
                    "huggingface_model_id": getattr(model, 'huggingface_model_id', ''),
                    "modelscope_model_id": getattr(model, 'modelscope_model_id', ''),
                    "model_series": model_series
                }
            except Exception as e:
                print(f"⚠️  Warning: Error extracting model {model_id}: {e}")
                continue
                
        return models
    except Exception as e:
        print(f"❌ Error importing models: {e}")
        return {}

def extract_instances():
    """Extract all instance definitions"""
    try:
        from emd.models.instances import Instance
        
        instances = {}
        for instance_type, instance in Instance.instance_map.items():
            try:
                instances[getattr(instance_type, 'value', str(instance_type))] = {
                    "instance_type": getattr(instance_type, 'value', str(instance_type)),
                    "gpu_num": getattr(instance, 'gpu_num', None),
                    "neuron_core_num": getattr(instance, 'neuron_core_num', None),
                    "vcpu": getattr(instance, 'vcpu', 0),
                    "memory": getattr(instance, 'memory', 0),
                    "description": getattr(instance, 'description', ''),
                    "support_cn_region": getattr(instance, 'support_cn_region', False)
                }
            except Exception as e:
                print(f"⚠️  Warning: Error extracting instance {instance_type}: {e}")
                continue
                
        return instances
    except Exception as e:
        print(f"❌ Error importing instances: {e}")
        return {}

def extract_engines():
    """Extract engine definitions and descriptions"""
    engines = {
        "vllm": {
            "engine_type": "vllm",
            "description": "vLLM - High-performance inference engine optimized for large language models",
            "support_inf2_instance": False
        },
        "huggingface": {
            "engine_type": "huggingface", 
            "description": "Hugging Face Transformers - Popular library for transformer models",
            "support_inf2_instance": False
        },
        "tgi": {
            "engine_type": "tgi",
            "description": "Text Generation Inference - Optimized inference server for text generation",
            "support_inf2_instance": True
        },
        "ollama": {
            "engine_type": "ollama",
            "description": "Ollama - Lightweight, high-performance model server",
            "support_inf2_instance": False
        },
        "llama.cpp": {
            "engine_type": "llama.cpp",
            "description": "llama.cpp - Efficient C++ implementation for LLaMA models",
            "support_inf2_instance": False
        },
        "lmdeploy": {
            "engine_type": "lmdeploy",
            "description": "LMDeploy - High-performance inference engine",
            "support_inf2_instance": False
        },
        "comfyui": {
            "engine_type": "comfyui",
            "description": "ComfyUI - Node-based interface for stable diffusion workflows",
            "support_inf2_instance": False
        },
        "ktransformers": {
            "engine_type": "ktransformers",
            "description": "KTransformers - Optimized transformer inference engine",
            "support_inf2_instance": False
        }
    }
    return engines

def extract_services():
    """Extract service definitions"""
    try:
        from emd.models.services import Service
        
        services = {}
        for service_type, service in Service.service_type_maps.items():
            try:
                services[getattr(service_type, 'value', str(service_type))] = {
                    "service_type": getattr(service_type, 'value', str(service_type)),
                    "name": getattr(service, 'name', ''),
                    "description": getattr(service, 'description', ''),
                    "support_cn_region": getattr(service, 'support_cn_region', False),
                    "need_vpc": getattr(service, 'need_vpc', False)
                }
            except Exception as e:
                print(f"⚠️  Warning: Error extracting service {service_type}: {e}")
                continue
                
        return services
    except Exception as e:
        print(f"❌ Error importing services: {e}")
        return {}

def generate_javascript_config():
    """Generate JavaScript configuration file"""
    try:
        print("🔄 Extracting EMD model configurations...")
        
        config = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "source": "EMD Python Model Definitions"
            },
            "models": extract_models(),
            "instances": extract_instances(), 
            "engines": extract_engines(),
            "services": extract_services()
        }
        
        # Generate JavaScript file content
        js_content = f"""// EMD Model Configuration
// Auto-generated from Python model definitions
// Generated at: {config['metadata']['generated_at']}

window.EMD_MODEL_CONFIG = {json.dumps(config, indent=2, ensure_ascii=False)};

// Helper functions for accessing configuration
window.EMD_HELPERS = {{
  getModel: function(modelId) {{
    return window.EMD_MODEL_CONFIG.models[modelId];
  }},
  
  getAllModels: function() {{
    return window.EMD_MODEL_CONFIG.models;
  }},
  
  getModelsByType: function(type) {{
    const models = {{}};
    for (const [id, model] of Object.entries(window.EMD_MODEL_CONFIG.models)) {{
      if (model.model_type === type) {{
        models[id] = model;
      }}
    }}
    return models;
  }},
  
  getInstance: function(instanceType) {{
    return window.EMD_MODEL_CONFIG.instances[instanceType];
  }},
  
  getEngine: function(engineType) {{
    return window.EMD_MODEL_CONFIG.engines[engineType];
  }},
  
  getService: function(serviceType) {{
    return window.EMD_MODEL_CONFIG.services[serviceType];
  }},
  
  getCompatibleInstances: function(modelId) {{
    const model = this.getModel(modelId);
    return model ? model.supported_instances : [];
  }},
  
  getCompatibleEngines: function(modelId) {{
    const model = this.getModel(modelId);
    return model ? model.supported_engines : [];
  }},
  
  getCompatibleServices: function(modelId) {{
    const model = this.getModel(modelId);
    return model ? model.supported_services : [];
  }},
  
  getModelCount: function() {{
    return Object.keys(window.EMD_MODEL_CONFIG.models).length;
  }},
  
  getGeneratedAt: function() {{
    return window.EMD_MODEL_CONFIG.metadata.generated_at;
  }},
  
  // Additional utility functions
  getModelsByEngine: function(engineType) {{
    const models = {{}};
    for (const [id, model] of Object.entries(window.EMD_MODEL_CONFIG.models)) {{
      if (model.supported_engines.includes(engineType)) {{
        models[id] = model;
      }}
    }}
    return models;
  }},
  
  getModelsByInstance: function(instanceType) {{
    const models = {{}};
    for (const [id, model] of Object.entries(window.EMD_MODEL_CONFIG.models)) {{
      if (model.supported_instances.includes(instanceType)) {{
        models[id] = model;
      }}
    }}
    return models;
  }},
  
  getModelsByService: function(serviceType) {{
    const models = {{}};
    for (const [id, model] of Object.entries(window.EMD_MODEL_CONFIG.models)) {{
      if (model.supported_services.includes(serviceType)) {{
        models[id] = model;
      }}
    }}
    return models;
  }},
  
  getChinaRegionModels: function() {{
    const models = {{}};
    for (const [id, model] of Object.entries(window.EMD_MODEL_CONFIG.models)) {{
      if (model.allow_china_region) {{
        models[id] = model;
      }}
    }}
    return models;
  }},
  
  getInstanceSpecs: function(instanceType) {{
    const instance = this.getInstance(instanceType);
    if (!instance) return null;
    
    const specs = [];
    if (instance.gpu_num) specs.push(`${{instance.gpu_num}} GPU`);
    if (instance.neuron_core_num) specs.push(`${{instance.neuron_core_num}} Neuron`);
    specs.push(`${{instance.vcpu}} vCPU`);
    specs.push(`${{instance.memory}} GiB`);
    
    return {{
      text: specs.join(', '),
      gpu_num: instance.gpu_num,
      neuron_core_num: instance.neuron_core_num,
      vcpu: instance.vcpu,
      memory: instance.memory
    }};
  }}
}};

console.log(`✅ EMD Model Configuration loaded: ${{window.EMD_HELPERS.getModelCount()}} models available`);
console.log(`📊 Model types: LLM (${{Object.keys(window.EMD_HELPERS.getModelsByType('llm')).length}}), VLM (${{Object.keys(window.EMD_HELPERS.getModelsByType('vlm')).length}}), Embedding (${{Object.keys(window.EMD_HELPERS.getModelsByType('embedding')).length}}), Whisper (${{Object.keys(window.EMD_HELPERS.getModelsByType('whisper')).length}})`);
"""
        
        # Write JavaScript file
        output_file = project_root / "docs" / "model_config.js"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(js_content)
        
        print(f"✅ Successfully extracted {len(config['models'])} models")
        print(f"✅ Successfully extracted {len(config['instances'])} instances")
        print(f"✅ Successfully extracted {len(config['engines'])} engines")
        print(f"✅ Successfully extracted {len(config['services'])} services")
        print(f"✅ JavaScript configuration saved to {output_file}")
        
        # Print some sample data for verification
        if config['models']:
            print("\n📋 Sample models extracted:")
            for i, (model_id, model) in enumerate(list(config['models'].items())[:5]):
                print(f"   {i+1}. {model_id} ({model['model_type']}) - {len(model['supported_instances'])} instances")
        
        if config['instances']:
            print(f"\n🖥️  Instance types: {', '.join(list(config['instances'].keys())[:10])}{'...' if len(config['instances']) > 10 else ''}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating model configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 EMD Model Configuration Generator")
    print("=" * 50)
    
    success = generate_javascript_config()
    
    if success:
        print("\n🎉 Configuration generation completed successfully!")
        print("📁 Output file: docs/model_config.js")
        print("🔗 Ready for integration with HTML interface")
    else:
        print("\n💥 Configuration generation failed!")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)