
FROM public.ecr.aws/aws-gcr-solutions/nvidia/cuda:12.2.0-base-ubuntu22.04
#FROM public.ecr.aws/ubuntu/ubuntu:22.04_stable

SHELL ["/bin/bash", "-c"]

WORKDIR /home/ubuntu/

RUN adduser --disabled-password --gecos '' ubuntu && \
    apt-get update -y && \
    apt-get install --no-install-recommends -y \
                    git libgl1 libtcmalloc-minimal4 libglib2.0-0 python3.10 python3.10-venv net-tools bc \
                    pkg-config file curl protobuf-compiler mesa-utils \
                    python3-dev libaio-dev libcairo2-dev libprotobuf-dev build-essential cmake wget ffmpeg && \
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
RUN wget -P /home/ubuntu/ComfyUI/models/loras https://d32oiauqot40oo.cloudfront.net/models/loras/flux-turbo-alpha.safetensors
RUN wget -P /home/ubuntu/ComfyUI/models/style_models https://huggingface.co/Runware/FLUX.1-Redux-dev/resolve/main/flux1-redux-dev.safetensors
RUN wget -P /home/ubuntu/ComfyUI/models/vae https://d32oiauqot40oo.cloudfront.net/models/vae/ae.safetensors
RUN mkdir /home/ubuntu/ComfyUI/models/BiRefNet 
RUN wget -P /home/ubuntu/ComfyUI/models/BiRefNet https://huggingface.co/ViperYX/BiRefNet/resolve/main/BiRefNet-ep480.pth
RUN wget -P /home/ubuntu/ComfyUI/models/BiRefNet https://huggingface.co/ViperYX/BiRefNet/resolve/main/swin_large_patch4_window12_384_22kto1k.pth                                                  
RUN wget -P /home/ubuntu/ComfyUI/models/loras https://huggingface.co/RiverZ/normal-lora/resolve/main/pytorch_lora_weights.safetensors
RUN wget -P /home/ubuntu/ComfyUI/models/unet https://huggingface.co/loremipsum3658/FluxRealistic/resolve/main/fluxRealisticSamayV2.WLdo.gguf
RUN wget -P /home/ubuntu/ComfyUI/models/loras https://huggingface.co/Zose22/public/resolve/main/flux-hand-v2.safetensors


RUN wget -qO '/home/ubuntu/ComfyUI/models/checkpoints/flux1-dev-fp8.safetensors' 'https://huggingface.co/lllyasviel/flux1_dev/resolve/main/flux1-dev-fp8.safetensors'
RUN wget -qO '/home/ubuntu/ComfyUI/models/loras/flux-realism-lora.safetensors' 'https://huggingface.co/XLabs-AI/flux-RealismLora/resolve/main/lora.safetensors'
RUN wget -qO '/home/ubuntu/ComfyUI/models/controlnet/flux_inpaint_beta.safetensors' 'https://huggingface.co/MikaelTradera/ae/resolve/b56b3ae98dc3873f4813d8d380812a0ba64a2619/FLUX.1-dev-Controlnet-Inpainting-Beta.safetensors'


# COPY src /home/ubuntu/src
# COPY src/deploy/on_sagemaker/serve /usr/bin/serve
# RUN chmod +x /usr/bin/serve
COPY backend/comfyui/bus_mask.png backend/comfyui/bus2.jpeg backend/comfyui/test_car.png backend/comfyui/girl_test.png /home/ubuntu/ComfyUI/input/

RUN apt-get update
RUN apt-get install -y python3-pip
RUN pip install uvicorn
RUN pip install fastapi
RUN pip install requests
RUN pip install boto3
RUN pip install aiohttp
RUN pip install websocket
RUN pip install websocket-client
RUN pip install pillow
RUN pip install botocore
# Set the serve script as the entrypoint
EXPOSE 8188
ENTRYPOINT ["/usr/bin/serve"]
