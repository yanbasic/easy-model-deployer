#!/bin/bash

echo "---------------------------------------------------------------------------------"
echo "install comfy..."

export INITIAL_COMFY_COMMIT_ROOT=e6609dacdeeafa371fe4e9f303016a605a333a76
export LTXV_COMMIT_ID=4c5add5f4693e5bf55b58aad99326fab9e9b4a53

rm -rf ComfyUI

git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI || exit 1
git reset --hard ${INITIAL_COMFY_COMMIT_ROOT}
cd ../

echo "---------------------------------------------------------------------------------"
echo "build comfy..."

cd ComfyUI || exit 1

git clone https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager
git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts custom_nodes/ComfyUI-Custom-Scripts 
git clone https://github.com/chflame163/ComfyUI_LayerStyle_Advance.git custom_nodes/ComfyUI_LayerStyle_Advance
git clone https://github.com/chflame163/ComfyUI_LayerStyle.git custom_nodes/ComfyUI_LayerStyle 
git clone https://github.com/rgthree/rgthree-comfy custom_nodes/rgthree-comfy 
git clone https://github.com/yolain/ComfyUI-Easy-Use custom_nodes/ComfyUI-Easy-Use
git clone https://github.com/WASasquatch/was-node-suite-comfyui custom_nodes/was-node-suite-comfyui
git clone https://github.com/kijai/ComfyUI-KJNodes custom_nodes/ComfyUI-KJNodes
git clone https://github.com/kijai/ComfyUI-Florence2 custom_nodes/ComfyUI-Florence2 
git clone https://github.com/cubiq/ComfyUI_essentials custom_nodes/ComfyUI_essentials 
git clone https://github.com/TTPlanetPig/Comfyui_Object_Migration custom_nodes/Comfyui_Object_Migration
git clone https://github.com/lquesada/ComfyUI-Inpaint-CropAndStitch custom_nodes/ComfyUI-Inpaint-CropAndStitch 
git clone https://github.com/HappyXY/ComfyUI-DiffBIR.git custom_nodes/ComfyUI-DiffBIR
git clone https://github.com/hayd-zju/ICEdit-ComfyUI-official.git custom_nodes/ICEdit-ComfyUI-official
git clone https://github.com/city96/ComfyUI-GGUF.git custom_nodes/ComfyUI-GGUF
git clone https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git custom_nodes/ComfyUI-Impact-Subpack
git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git custom_nodes/ComfyUI-Impact-Pack


git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git custom_nodes/ComfyUI-VideoHelperSuite
git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git custom_nodes/ComfyUI-LTXVideo
cd custom_nodes/ComfyUI-LTXVideo || exit 1
git reset --hard "$LTXV_COMMIT_ID"
cd ../../

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install boto3
pip install aws_xray_sdk
pip install fastapi
pip install uvicorn
pip install watchdog
pip install python-dotenv
pip install httpx
pip install onnxruntime
pip install diffusers
pip install sentencepiece
pip install insightface==0.7.3
pip install opencv-python

pip install -r custom_nodes/ComfyUI-Manager/requirements.txt
# pip install -r custom_nodes/ComfyUI-Custom-Scripts/requirements.txt
pip install -r custom_nodes/ComfyUI_LayerStyle_Advance/requirements.txt
pip install -r custom_nodes/rgthree-comfy/requirements.txt
pip install -r custom_nodes/ComfyUI-Easy-Use/requirements.txt
pip install -r custom_nodes/was-node-suite-comfyui/requirements.txt
pip install -r custom_nodes/ComfyUI-KJNodes/requirements.txt
pip install -r custom_nodes/ComfyUI-Florence2/requirements.txt
pip install -r custom_nodes/ComfyUI_essentials/requirements.txt
pip install -r custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt
pip install av>=10.0.0
pip install ltx-video@git+https://github.com/Lightricks/LTX-Video@ltx-video-0.9.1
pip install -r custom_nodes/ComfyUI-DiffBIR/requirements.txt
pip install -r custom_nodes/ComfyUI-GGUF/requirements.txt
pip install -r custom_nodes/ComfyUI-Impact-Subpack/requirements.txt
pip install -r custom_nodes/ComfyUI-Impact-Pack/requirements.txt

pip install https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip
pip install https://github.com/mlfoundations/open_clip/archive/bb6e834e9c70d9c27d0dc3ecedeebeaeb1ffad6b.zip
pip install protobuf==3.20.2
pip install open-clip-torch==2.20.0
pip install xformers
pip install torchaudio
pip install transformers -U
pip install accelerate
pip install omegaconf

mkdir models/ultralytics
mkdir models/ultralytics/bbox
wget -P models/ultralytics/bbox https://huggingface.co/Bingsu/adetailer/resolve/main/hand_yolov9c.pt

mkdir models/clip
wget -P models/clip https://huggingface.co/calcuis/hunyuan-gguf/resolve/main/clip_l.safetensors
wget -P models/clip https://huggingface.co/calcuis/sd3.5-large-gguf/resolve/main/t5xxl_fp8_e4m3fn.safetensors
mkdir models/clip_vision
wget -P models/clip_vision https://huggingface.co/Comfy-Org/sigclip_vision_384/resolve/main/sigclip_vision_patch14_384.safetensors
mkdir models/diffusion_models
wget -P models/diffusion_models https://huggingface.co/second-state/FLUX.1-Fill-dev-GGUF/resolve/main/flux1-fill-dev.safetensors
mkdir models/loras
wget -P models/loras https://huggingface.co/ali-vilab/ACE_Plus/resolve/main/subject/comfyui_subject_lora16.safetensors
wget -P models/loras https://d32oiauqot40oo.cloudfront.net/models/loras/flux-turbo-alpha.safetensors
mkdir models/style_models
wget -P models/style_models https://huggingface.co/Runware/FLUX.1-Redux-dev/resolve/main/flux1-redux-dev.safetensors
mkdir models/vae
wget -P models/vae https://d32oiauqot40oo.cloudfront.net/models/vae/ae.safetensors
mkdir models/BiRefNet 
wget -P models/BiRefNet https://huggingface.co/ViperYX/BiRefNet/resolve/main/BiRefNet-ep480.pth
wget -P models/BiRefNet https://huggingface.co/ViperYX/BiRefNet/resolve/main/swin_large_patch4_window12_384_22kto1k.pth                                                  
mkdir models/LLM
wget -P models/loras https://huggingface.co/RiverZ/normal-lora/resolve/main/pytorch_lora_weights.safetensors
wget -P models/unet https://huggingface.co/loremipsum3658/FluxRealistic/resolve/main/fluxRealisticSamayV2.WLdo.gguf
wget -P models/loras https://huggingface.co/Zose22/public/resolve/main/flux-hand-v2.safetensors