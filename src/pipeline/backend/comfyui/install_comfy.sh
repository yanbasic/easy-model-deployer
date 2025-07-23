#!/bin/bash

echo "---------------------------------------------------------------------------------"
echo "install comfy..."

export INITIAL_COMFY_COMMIT_ROOT=c5de4955bb91a2b136027a698aaecb8d19e3d892
#e6609dacdeeafa371fe4e9f303016a605a333a76
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


pip install --upgrade pip
pip install -r requirements.txt

pip install -r custom_nodes/ComfyUI-Manager/requirements.txt
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