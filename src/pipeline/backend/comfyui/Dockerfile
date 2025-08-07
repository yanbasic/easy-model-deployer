
FROM public.ecr.aws/aws-gcr-solutions/nvidia/cuda:12.2.0-base-ubuntu22.04
#FROM public.ecr.aws/ubuntu/ubuntu:22.04_stable

SHELL ["/bin/bash", "-c"]

WORKDIR /home/ubuntu/

RUN adduser --disabled-password --gecos '' ubuntu && \
    apt-get update -y && \
    apt-get install --no-install-recommends -y \
                    git libgl1 libtcmalloc-minimal4 libglib2.0-0 python3.10 python3.10-venv net-tools bc \
                    pkg-config file curl protobuf-compiler mesa-utils \
                    python3-dev libaio-dev libcairo2-dev libprotobuf-dev build-essential cmake wget ffmpeg \
                    python3-pip python-is-python3 && \
    rm -rf /var/lib/apt/lists/* && \
    wget -q https://github.com/peak/s5cmd/releases/download/v2.2.2/s5cmd_2.2.2_Linux-64bit.tar.gz && \
    tar xzvf s5cmd_2.2.2_Linux-64bit.tar.gz && \
    rm -rf s5cmd_2.2.2_Linux-64bit.tar.gz && \
    mv s5cmd /usr/local/bin/


ENV ESD_COMMIT_ID=dev
ENV ON_SAGEMAKER true
ENV LD_PRELOAD /usr/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4

RUN mkdir -p /home/ubuntu/conda/lib/ && \
    wget -qO /home/ubuntu/conda/lib/libcufft.so.10 https://huggingface.co/elonniu/esd/resolve/main/libcufft.so.10 && \
    wget -qO /home/ubuntu/conda/lib/libcurand.so.10 https://huggingface.co/elonniu/esd/resolve/main/libcurand.so.10

COPY backend/comfyui/install_comfy.sh /home/ubuntu/
#COPY trim_comfy.sh /home/ubuntu/

COPY backend/comfyui/start.sh /
RUN chmod +x /start.sh


RUN cd /home/ubuntu || exit 1 && \
    bash install_comfy.sh

RUN mkdir /home/ubuntu/ComfyUI/models/ultralytics
RUN mkdir /home/ubuntu/ComfyUI/models/ultralytics/bbox
RUN wget -P /home/ubuntu/ComfyUI/models/ultralytics/bbox https://huggingface.co/Bingsu/adetailer/resolve/main/hand_yolov9c.pt

RUN wget -P /home/ubuntu/ComfyUI/models/clip https://huggingface.co/calcuis/hunyuan-gguf/resolve/main/clip_l.safetensors
RUN wget -P /home/ubuntu/ComfyUI/models/clip https://huggingface.co/calcuis/sd3.5-large-gguf/resolve/main/t5xxl_fp8_e4m3fn.safetensors
RUN wget -P /home/ubuntu/ComfyUI/models/clip_vision https://huggingface.co/Comfy-Org/sigclip_vision_384/resolve/main/sigclip_vision_patch14_384.safetensors
RUN wget -P /home/ubuntu/ComfyUI/models/diffusion_models https://huggingface.co/second-state/FLUX.1-Fill-dev-GGUF/resolve/main/flux1-fill-dev.safetensors
RUN wget -P /home/ubuntu/ComfyUI/models/loras https://huggingface.co/ali-vilab/ACE_Plus/resolve/main/subject/comfyui_subject_lora16.safetensors
RUN wget -P /home/ubuntu/ComfyUI/models/style_models https://huggingface.co/Runware/FLUX.1-Redux-dev/resolve/main/flux1-redux-dev.safetensors
RUN mkdir /home/ubuntu/ComfyUI/models/BiRefNet 
RUN wget -P /home/ubuntu/ComfyUI/models/BiRefNet https://huggingface.co/ViperYX/BiRefNet/resolve/main/BiRefNet-ep480.pth
RUN wget -P /home/ubuntu/ComfyUI/models/BiRefNet https://huggingface.co/ViperYX/BiRefNet/resolve/main/swin_large_patch4_window12_384_22kto1k.pth                                                  
RUN wget -P /home/ubuntu/ComfyUI/models/loras https://huggingface.co/RiverZ/normal-lora/resolve/main/pytorch_lora_weights.safetensors
RUN wget -P /home/ubuntu/ComfyUI/models/unet https://huggingface.co/loremipsum3658/FluxRealistic/resolve/main/fluxRealisticSamayV2.WLdo.gguf
RUN wget -P /home/ubuntu/ComfyUI/models/loras https://huggingface.co/Zose22/public/resolve/main/flux-hand-v2.safetensors

RUN wget -qO '/home/ubuntu/ComfyUI/models/loras/flux-realism-lora.safetensors' 'https://huggingface.co/XLabs-AI/flux-RealismLora/resolve/main/lora.safetensors'
RUN wget -qO '/home/ubuntu/ComfyUI/models/controlnet/flux_inpaint_beta.safetensors' 'https://huggingface.co/MikaelTradera/ae/resolve/b56b3ae98dc3873f4813d8d380812a0ba64a2619/FLUX.1-dev-Controlnet-Inpainting-Beta.safetensors'
RUN wget -qO '/home/ubuntu/ComfyUI/models/diffusion_models/flux1-dev-kontext_fp8_scaled.safetensors' 'https://huggingface.co/Comfy-Org/flux1-kontext-dev_ComfyUI/resolve/main/split_files/diffusion_models/flux1-dev-kontext_fp8_scaled.safetensors'
RUN wget -qO '/home/ubuntu/ComfyUI/models/loras/flux-turbo-alpha.safetensors' 'https://huggingface.co/alimama-creative/FLUX.1-Turbo-Alpha/resolve/main/diffusion_pytorch_model.safetensors'
RUN wget -qO '/home/ubuntu/ComfyUI/models/vae/ae.safetensors' 'https://huggingface.co/ffxvs/vae-flux/resolve/main/ae.safetensors'


# add node comfyui-teacache
RUN cd /home/ubuntu/ComfyUI/custom_nodes && \
    git clone https://github.com/welltop-cn/ComfyUI-TeaCache.git && \
    cd ComfyUI-TeaCache && \
    pip install -r requirements.txt

# Clone Comfyui-PaddleOCR (this layer can be cached)
RUN cd /home/ubuntu/ComfyUI/custom_nodes && \
    git clone https://github.com/HappyXY/Comfyui-PaddleOCR.git && \
    cd Comfyui-PaddleOCR && \
    git submodule update --init --recursive

RUN cd /home/ubuntu/ComfyUI/custom_nodes && \
    git clone https://github.com/HappyXY/ComfyUI-AmazonBedrock.git

COPY backend/comfyui/bus_mask.png backend/comfyui/bus2.jpeg backend/comfyui/test_car.png backend/comfyui/girl_test.png /home/ubuntu/ComfyUI/input/


RUN pip install requests retry aiohttp websocket-client pillow botocore \
                boto3 aws_xray_sdk fastapi uvicorn watchdog python-dotenv httpx \
                onnxruntime diffusers sentencepiece "insightface==0.7.3" opencv-python \
                "protobuf==3.20.2" "open-clip-torch==2.20.0" xformers torchaudio \
                accelerate omegaconf "paddleocr==3.0.2" && \
    pip install transformers -U && \
    pip install paddlepaddle-gpu==3.1.0 -i "https://www.paddlepaddle.org.cn/packages/stable/cu126/" && \
    pip install "https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip" && \
    pip install "https://github.com/mlfoundations/open_clip/archive/bb6e834e9c70d9c27d0dc3ecedeebeaeb1ffad6b.zip"


RUN cd /home/ubuntu/ComfyUI/custom_nodes && \
    git clone https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes.git

RUN cd /home/ubuntu/ComfyUI/custom_nodes && \
git clone https://github.com/2kpr/ComfyUI-PMRF.git

RUN pip install natten==0.17.5+torch260cu126 -f https://whl.natten.org

# Add cache-busting ARG at the very end to minimize impact
ARG CACHE_BUST=1

# Update Comfyui-PaddleOCR (this will always run and only affect the final layers)
RUN cd /home/ubuntu/ComfyUI/custom_nodes/Comfyui-PaddleOCR && \
    git fetch --all && \
    git reset --hard origin/main && \
    git pull

# Remove the separate git pull command since it's now combined with the clone operation above


# Set the serve script as the entrypoint
EXPOSE 8188
ENTRYPOINT ["/usr/bin/serve"]
