import os
import copy
import time
import json
import uuid
import io
import base64

from typing import Optional
from pydantic import ValidationError
from backend.backend import BackendBase
from typing import Iterable, List
import requests
import boto3
import logging
from aiohttp import web
import websocket
from botocore.client import Config
from PIL import Image

from utils.common import sync_s3_files_or_folders_to_local, sync_local_outputs_to_s3


# ROOT_PATH = '/home/ubuntu/ComfyUI'
ROOT_PATH = "ComfyUI"
SERVER_ADDRESS = "127.0.0.1:8188"
URL_PING = f"http://{SERVER_ADDRESS}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ok(body: dict):
    return web.Response(
        status=200, content_type="application/json", body=json.dumps(body)
    )


class ComfyUIBackend(BackendBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_id = self.execute_model.model_id
        self.model_s3_bucket = self.execute_model.executable_config.model_s3_bucket
        self.api_base = f"{URL_PING}/prompt"
        self.s3_client = boto3.client("s3")
        self.client_id = str(uuid.uuid4())
        environ = {}  # Environment dictionary
        socket = None  # Socket object
        rfile = None  # File-like object for reading
        self.ws = websocket.WebSocket(environ, socket, rfile)
        with open("backend/comfyui/ltxvideo-txt2video-api.json") as f:
            self.workflow = json.load(f)
        self.bedrock_runtime_client_image = boto3.client(
            "bedrock-runtime",
            region_name="us-east-1",
            config=Config(
            read_timeout=5 * 60
            ),
        )
        self.image_generation_model_id = "amazon.nova-canvas-v1:0"

    def start(self):
        # model_dir = f"emd_models/{self.model_id}"
        # logger.info(f"Downloading model from s3")
        # sync_s3_files_or_folders_to_local(self.model_s3_bucket, model_dir, ROOT_PATH)

        os.system("bash backend/comfyui/start.sh > comfyui.log 2>&1 &")
        while True:
            try:
                self.ws.connect(
                    "ws://{}/ws?clientId={}".format(SERVER_ADDRESS, self.client_id)
                )
                logger.info(f"Connected to comfyui websocket")
                break
            except Exception as e:
                logger.info(
                    f"The comfyui websocket is not ready yet, retrying in 10 second"
                )
                time.sleep(10)
                continue
        return

    def _remove_background(self, reference_image_base64):
        body = json.dumps(
            {
                "taskType": "BACKGROUND_REMOVAL",
                "backgroundRemovalParams": {"image": reference_image_base64},
            }
        )
        print("Generating image...")
        try:
            response = self.bedrock_runtime_client_image.invoke_model(
                body=body,
                modelId=self.image_generation_model_id,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            return response_body
        except Exception as e:
            print(f"Error during background removal: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _text2img(self, prompt, negative_prompt, width, height, num_imgs, seed=1):
        # Generate image using only a text prompt.
        body = json.dumps(
            {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt, # A description of the final desired image
                    "negativeText": negative_prompt,  # What to avoid generating inside the mask
                },
                "imageGenerationConfig": {
                    "numberOfImages": num_imgs,  # Number of images to generate, up to 5
                    "width": width,
                    "height": height,
                    "cfgScale": 6.5,  # How closely the prompt will be followed
                    "seed": seed,  # Any number from 0 through 858,993,459
                    "quality": "premium",  # Quality of either "standard" or "premium"
                },
            }
        )
        print("Generating image...")
        try:
            response = self.bedrock_runtime_client_image.invoke_model(
                body=body,
                modelId=self.image_generation_model_id,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            return response_body
        except Exception as e:
            print(f"Error during background removal: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _image_variation(self, reference_image_base64, prompt, negative_prompt, width, height, num_imgs, similarity_strength=0.5, seed=1):
    
        print("Generating image with a reference image...")

        # Generate image with referece (Image variation feature)
        body=json.dumps(
            {
                "taskType": "IMAGE_VARIATION",
                "imageVariationParams": {
                    "text": prompt,
                    "negativeText": negative_prompt,  # What to avoid generating inside the image
                    "images": [
                        reference_image_base64
                    ],  # May provide up to 5 reference images here
                    "similarityStrength": similarity_strength,  # How strongly the input images influence the output. From 0.2 through 1.
                },
                "imageGenerationConfig": {
                    "numberOfImages": num_imgs,  # Number of images to generate, up to 5.
                    "cfgScale": 6.5,  # How closely the prompt will be followed
                    "seed": seed,  # Any number from 0 through 858,993,459
                    "width": width,
                    "height": height,
                    "quality": "standard",  # Either "standard" or "premium". Defaults to "standard".
                },
            }
        )

        print("Generating image...")
        try:
            response = self.bedrock_runtime_client_image.invoke_model(
                body=body,
                modelId=self.image_generation_model_id,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            return response_body
        except Exception as e:
            print(f"Error during background removal: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _image_color_conditioning(self, colors, prompt, negative_prompt, width, height, num_imgs, seed=1):
        print("Generating image with a reference image...")

        # Generate image with referece (Image color conditioning feature)
        body = json.dumps(
            {
                "taskType": "COLOR_GUIDED_GENERATION",
                "colorGuidedGenerationParams": {
                    "text": prompt,
                    "negativeText": negative_prompt,  # What to avoid generating inside the image
                    "colors": colors,
                },
                "imageGenerationConfig": {
                    "numberOfImages": num_imgs,  # Number of images to generate, up to 5
                    "cfgScale": 6.5,  # How closely the prompt will be followed
                    "width": width,
                    "height": height,
                    "seed": seed,
                    "quality": "standard",  # Quality of either "standard" or "premium"
                },
            }
        )
        print("Generating image...")
        try:
            response = self.bedrock_runtime_client_image.invoke_model(
                body=body,
                modelId=self.image_generation_model_id,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            return response_body
        except Exception as e:
            print(f"Error during background removal: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _outpaint_with_maskPrompt(self, reference_image_base64, prompt, negative_prompt, mask_prompt, num_imgs, seed=1):
        # Generate image condition on reference image
        body = json.dumps(
            {
            "taskType": "OUTPAINTING",
            "outPaintingParams": {
                "text": prompt,  # A description of the final desired image
                "negativeText": negative_prompt,  # What to avoid generating inside the mask
                "image": reference_image_base64,  # The image to edit
                "maskPrompt": mask_prompt,  # One of "maskImage" or "maskPrompt" is required
                "outPaintingMode": "PRECISE",  # Either "DEFAULT" or "PRECISE"
            },
            "imageGenerationConfig": {
                "numberOfImages": num_imgs,  # Number of images to generate, up to 5.
                "cfgScale": 6.5,  # How closely the prompt will be followed
                "seed": seed,  # Any number from 0 through 858,993,459
                "quality": "standard",  # Either "standard" or "premium". Defaults to "standard".
            },
        }
        )

        print("Generating image...")
        try:
            response = self.bedrock_runtime_client_image.invoke_model(
                body=body,
                modelId=self.image_generation_model_id,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            return response_body
        except Exception as e:
            print(f"Error during background removal: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _outpaint_with_maskImage(self, reference_image_base64, prompt, negative_prompt, mask_image_base64, num_imgs, seed=1):
        # Generate image condition on reference image
        body = json.dumps(
            {
            "taskType": "OUTPAINTING",
            "outPaintingParams": {
                "text": prompt,  # A description of the final desired image
                "negativeText": negative_prompt,  # What to avoid generating inside the mask
                "image": reference_image_base64,  # The image to edit
                "maskImage": mask_image_base64,  # One of "maskImage" or "maskPrompt" is required
                "outPaintingMode": "DEFAULT",  # Either "DEFAULT" or "PRECISE"
            },
            "imageGenerationConfig": {
                "numberOfImages": num_imgs,  # Number of images to generate, up to 5.
                "cfgScale": 6.5,  # How closely the prompt will be followed
                "seed": seed,  # Any number from 0 through 858,993,459
                "quality": "standard",  # Either "standard" or "premium". Defaults to "standard".
            },
        }
        )

        print("Generating image...")
        try:
            response = self.bedrock_runtime_client_image.invoke_model(
                body=body,
                modelId=self.image_generation_model_id,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            return response_body
        except Exception as e:
            print(f"Error during background removal: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _replace_object_with_maskPrompt(self, reference_image_base64, prompt, negative_prompt, mask_prompt, num_imgs, seed=1):
        """
        Remove an object from the image using the specified prompt.
        """
        body = json.dumps(
            {
                "taskType": "INPAINTING",
                "inPaintingParams": {
                    "text": prompt,  # What to generate in the masked area
                    "negativeText": negative_prompt,  # What to avoid generating inside the mask
                    "image": reference_image_base64,  # The image to edit
                    "maskPrompt": mask_prompt,  # A description of the area(s) of the image to change
                },
                "imageGenerationConfig": {
                    "numberOfImages": num_imgs,  # Number of images to generate, up to 5.
                    "cfgScale": 6.5,  # How closely the prompt will be followed
                    "seed": seed,  # Any number from 0 through 858,993,459
                    "quality": "standard",  # Either "standard" or "premium". Defaults to "standard".
                },
            }
        )


        print("Generating image...")
        try:
            response = self.bedrock_runtime_client_image.invoke_model(
                body=body,
                modelId=self.image_generation_model_id,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            return response_body
        except Exception as e:
            print(f"Error during background removal: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _replace_object_with_maskImage(self, reference_image_base64, prompt, negative_prompt, mask_image_base64, num_imgs, seed=1):
        """
        Remove an object from the image using the specified mask image.
        """
        body = json.dumps(
            {
                "taskType": "INPAINTING",
                "inPaintingParams": {
                    "text": prompt,  # What to generate in the masked area
                    "negativeText": negative_prompt,  # What to avoid generating inside the mask
                    "image": reference_image_base64,  # The image to edit
                    "maskImage": mask_image_base64,  # The mask image to use
                },
                "imageGenerationConfig": {
                    "numberOfImages": num_imgs,  # Number of images to generate, up to 5.
                    "cfgScale": 6.5,  # How closely the prompt will be followed
                    "seed": seed,  # Any number from 0 through 858,993,459
                    "quality": "standard",  # Either "standard" or "premium". Defaults to "standard".
                },
            }
        )

        print("Generating image...")
        try:
            response = self.bedrock_runtime_client_image.invoke_model(
                body=body,
                modelId=self.image_generation_model_id,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            return response_body
        except Exception as e:
            print(f"Error during background removal: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _remove_object_with_maskPrompt(self, reference_image_base64, negative_prompt, mask_prompt, num_imgs, seed=1):
        """
        Remove an object from the image using the specified prompt.
        """
        body = json.dumps(
            {
                "taskType": "INPAINTING",
                "inPaintingParams": {
                    "negativeText": negative_prompt,  # What to avoid generating inside the mask
                    "image": reference_image_base64,  # The image to edit
                    "maskPrompt": mask_prompt,  # A description of the area(s) of the image to change
                },
                "imageGenerationConfig": {
                    "numberOfImages": num_imgs,  # Number of images to generate, up to 5.
                    "cfgScale": 6.5,  # How closely the prompt will be followed
                    "seed": seed,  # Any number from 0 through 858,993,459
                    "quality": "standard",  # Either "standard" or "premium". Defaults to "standard".
                },
            }
        )


        print("Generating image...")
        try:
            response = self.bedrock_runtime_client_image.invoke_model(
                body=body,
                modelId=self.image_generation_model_id,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            return response_body
        except Exception as e:
            print(f"Error during background removal: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _remove_object_with_maskImage(self, reference_image_base64, negative_prompt, mask_image_base64, num_imgs, seed=1):
        """
        Remove an object from the image using the specified mask image.
        """
        body = json.dumps(
            {
                "taskType": "INPAINTING",
                "inPaintingParams": {
                    "negativeText": negative_prompt,  # What to avoid generating inside the mask
                    "image": reference_image_base64,  # The image to edit
                    "maskImage": mask_image_base64,  # The mask image to use
                },
                "imageGenerationConfig": {
                    "numberOfImages": num_imgs,  # Number of images to generate, up to 5.
                    "cfgScale": 6.5,  # How closely the prompt will be followed
                    "seed": seed,  # Any number from 0 through 858,993,459
                    "quality": "standard",  # Either "standard" or "premium". Defaults to "standard".
                },
            }
        )

        print("Generating image...")
        try:
            response = self.bedrock_runtime_client_image.invoke_model(
                body=body,
                modelId=self.image_generation_model_id,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            return response_body
        except Exception as e:
            print(f"Error during background removal: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _generate_video_by_ltxvideo(self, prompt):
        workflow = copy.deepcopy(self.workflow)
        # Replace the prompt in the workflow
        # workflow["120"]["inputs"]["text"] = prompt
        # Add the prompt to video generation
        workflow["87"]["inputs"]["text"] += prompt
        comfyui_req = {"prompt": workflow, "client_id": self.client_id}
        self._invoke_comfyui(comfyui_req)

    def _ainvoke_comfyui(self, comfyui_req):
        data = json.dumps(comfyui_req).encode("utf-8")
        print(data)
        response = requests.post(self.api_base, data=data)
        response_data = response.json()
        print(response_data)
        prompt_id = response_data["prompt_id"]
        out_path = response_data.get("out_path", None)
        logger.info(f"prompt_id is {prompt_id}")
        # logger.info(f'out_path is {out_path}')
        s3_out_path = (
            f"output/{prompt_id}/{out_path}"
            if out_path is not None
            else f"output/{prompt_id}"
        )
        s3_temp_path = (
            f"temp/{prompt_id}/{out_path}"
            if out_path is not None
            else f"temp/{prompt_id}"
        )
        local_out_path = (
            f"{ROOT_PATH}/output/{out_path}"
            if out_path is not None
            else f"{ROOT_PATH}/output"
        )
        # local_temp_path = f'{ROOT_PATH}/temp/{out_path}' if out_path is not None else f'{ROOT_PATH}/temp'
        logger.info(
            f"s3_out_path is {s3_out_path} and local_out_path is {local_out_path}"
        )
        try:
            while True:
                out = self.ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    print("!!!!!!!!", message["type"])
                    if message["type"] == "executing":
                        data = message["data"]
                        print(data["prompt_id"])
                        if data["node"] is None and data["prompt_id"] == prompt_id:
                            logger.info(f"Execution is done for prompt_id {prompt_id}")
                            break  # Execution is done
                else:
                    continue  # previews are binary data
            # logger.info(f"Start to sync outputs to s3 for prompt_id {prompt_id}")
            sync_local_outputs_to_s3(self.model_s3_bucket, s3_out_path, local_out_path)
            # sync_local_outputs_to_s3(self.model_s3_bucket, s3_temp_path, local_temp_path)
            logger.info(f"Sync done to s3 for prompt_id {prompt_id}")
            response_body = {
                "prompt_id": prompt_id,
                "status": "success",
                "output_path": f"s3://{self.model_s3_bucket}/comfy/{s3_out_path}",
                # "temp_path": f's3://{self.model_s3_bucket}/comfy/{s3_temp_path}',
            }
            logger.info(f"execute inference response is {response_body}")
            return response_body
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            raise

    def _invoke_comfyui(self, comfyui_req):
        data = json.dumps(comfyui_req).encode("utf-8")
        response = requests.post(self.api_base, data=data)
        response_data = response.json()
        return response_data

    def invoke(self, request):
        if "taskType" in request:
            if request["taskType"] == "BACKGROUND_REMOVAL":
                response = self._remove_background(request["backgroundRemovalParams"]["image"])
                return response
            elif request["taskType"] == "VIDEO_GENERATION":
                self._generate_video_by_ltxvideo(request["videoGenerationParams"]["prompt"])
                return {"status": "success", "message": "Video generation started"}
            elif request["taskType"] == "TEXT_TO_IMAGE":
                print("!!!!!!!!!! Generating image with text prompt...")
                response = self._text2img(
                    request["textToImageParams"]["text"],
                    request["textToImageParams"].get("negativeText", ""),
                    request["imageGenerationConfig"]["width"],
                    request["imageGenerationConfig"]["height"],
                    request["imageGenerationConfig"]["numberOfImages"],
                    request["imageGenerationConfig"].get("seed", 1),
                )
                return response
            elif request["taskType"] == "IMAGE_VARIATION":
                response = self._image_variation(
                    request["imageVariationParams"]["images"][0],
                    request["imageVariationParams"]["text"],
                    request["imageVariationParams"].get("negativeText", ""),
                    request["imageGenerationConfig"]["width"],
                    request["imageGenerationConfig"]["height"],
                    request["imageGenerationConfig"]["numberOfImages"],
                    request["imageVariationParams"].get("similarityStrength", 0.5),
                    request["imageGenerationConfig"].get("seed", 1),
                )
                return self._get_response(response)
            elif request["taskType"] == "COLOR_GUIDED_GENERATION":
                response = self._image_color_conditioning(
                    request["colorGuidedGenerationParams"]["colors"],
                    request["colorGuidedGenerationParams"]["text"],
                    request["colorGuidedGenerationParams"].get("negativeText", ""),
                    request["imageGenerationConfig"]["width"],
                    request["imageGenerationConfig"]["height"],
                    request["imageGenerationConfig"]["numberOfImages"],
                    request["imageGenerationConfig"].get("seed", 1),
                )
                return self._get_response(response)
            elif request["taskType"] == "OUTPAINTING":
                if "maskPrompt" in request["outPaintingParams"]:
                    response = self._outpaint_with_maskPrompt(
                        request["outPaintingParams"]["image"],
                        request["outPaintingParams"]["text"],
                        request["outPaintingParams"].get("negativeText", ""),
                        request["outPaintingParams"]["maskPrompt"],
                        request["imageGenerationConfig"]["numberOfImages"],
                        request["imageGenerationConfig"].get("seed", 1),
                    )
                elif "maskImage" in request["outPaintingParams"]:
                    response = self._outpaint_with_maskImage(
                        request["outPaintingParams"]["image"],
                        request["outPaintingParams"]["text"],
                        request["outPaintingParams"].get("negativeText", ""),
                        request["outPaintingParams"]["maskImage"],
                        request["imageGenerationConfig"]["numberOfImages"],
                        request["imageGenerationConfig"].get("seed", 1),
                    )
                else:
                    raise ValueError("Either maskPrompt or maskImage must be provided")
                return self._get_response(response)
            elif request["taskType"] == "REPLACE_OBJECT":
                if "maskPrompt" in request["inPaintingParams"]:
                    response = self._replace_object_with_maskPrompt(
                        request["inPaintingParams"]["image"],
                        request["inPaintingParams"]["text"],
                        request["inPaintingParams"].get("negativeText", ""),
                        request["inPaintingParams"]["maskPrompt"],
                        request["imageGenerationConfig"]["numberOfImages"],
                        request["imageGenerationConfig"].get("seed", 1),
                    )
                elif "maskImage" in request["inPaintingParams"]:
                    response = self._replace_object_with_maskImage(
                        request["inPaintingParams"]["image"],
                        request["inPaintingParams"]["text"],
                        request["inPaintingParams"].get("negativeText", ""),
                        request["inPaintingParams"]["maskImage"],
                        request["imageGenerationConfig"]["numberOfImages"],
                        request["imageGenerationConfig"].get("seed", 1),
                    )
                else:
                    raise ValueError("Either maskPrompt or maskImage must be provided")
                return self._get_response(response)
            elif request["taskType"] == "REMOVE_OBJECT":
                if "maskPrompt" in request["inPaintingParams"]:
                    response = self._remove_object_with_maskPrompt(
                        request["inPaintingParams"]["image"],
                        request["inPaintingParams"].get("negativeText", ""),
                        request["inPaintingParams"]["maskPrompt"],
                        request["imageGenerationConfig"]["numberOfImages"],
                        request["imageGenerationConfig"].get("seed", 1),
                    )
                elif "maskImage" in request["inPaintingParams"]:
                    response = self._remove_object_with_maskImage(
                        request["inPaintingParams"]["image"],
                        request["inPaintingParams"].get("negativeText", ""),
                        request["inPaintingParams"]["maskImage"],
                        request["imageGenerationConfig"]["numberOfImages"],
                        request["imageGenerationConfig"].get("seed", 1),
                    )
                else:
                    raise ValueError("Either maskPrompt or maskImage must be provided")
                return self._get_response(response)
            elif request["taskType"] == "WORKFLOW":
                return self._invoke_comfyui(request["workflow"])
            else:
                raise ValueError("Invalid taskType")
        else:
            raise ValueError("Invalid request")

    def _transform_request(self, request):
        raise NotImplementedError

    def _transform_response(self, response):
        raise NotImplementedError

    def _get_response(self, response) -> List[str]:
        output = response
        return output
