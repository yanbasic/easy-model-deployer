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

        self.multimodal_model_id = "us.amazon.nova-premier-v1:0"
        self.video_model_id = "us.amazon.nova-reel-v1:1"

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
                    "images": reference_image_base64,  # May provide up to 5 reference images here
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

    def _image_analysis(self, reference_image_base64, img_format="png"):
        # use nova premier model to analyze the product image
        # nova premier first analyze the product image: 
        # the main object, the background, the style, and other useful information
        print(f"Initialized Bedrock client with model: {self.multimodal_model_id}")
        # Here you would implement the logic to call the Bedrock model
        print('img_format:', img_format)
        system_list = [
            {"text": """You are an expert in product image analysis and prompt generation.
                        Analyze this product image in detail:
                        1. Identify the main object/product
                        2. Describe the background
                        3. Analyze the visual style and composition
                        4. Analyze the color tone of the reference image, extract the main colors in the picture, and describe the color list using hexadecimal notation, for example, [#00ff91, #FF9900].
                        4. Note any other useful information (lighting, angle, etc.)

                        Then generate a comprehensive prompt for creating a similar image with:
                        - Detailed description of the product
                        - Style specifications
                        - Background elements
                        - Lighting and atmosphere
                        - Composition guidelines

                        Format your response as a JSON dictionary with these keys:
                        - product_name: the name of the product
                        - category: the category of the product
                        - style: the style of the product
                        - background: the background of the product
                        - color_list: the main colors, a list of hexadecimal notation
                        - prompt: the full prompt for similar image generation (less than 800 tokens)
                        """
            }
        ]
        inf_params = {
            "max_new_tokens": 1000,
            "top_p": 0.99,
            "top_k": 20,
            "temperature": 0.7
            }
        messages = [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "image":{
                                        "format": img_format,
                                        "source": {"bytes": reference_image_base64},
                                    }
                                },
                            ]
                        }
                    ]
        try:
            response = self.bedrock_runtime_client_image.invoke_model(
                modelId=self.multimodal_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "inferenceConfig": inf_params,
                    "messages": messages,
                    "system": system_list
                })
            )
            response_body = json.loads(response.get('body').read())
            content = response_body["output"]["message"]["content"][0]["text"]
            if content:
                # Check if the response is a JSON string
                if isinstance(content, str):
                    # Decode the content
                    text_content = content #.encode('utf-8').decode('unicode_escape')
                    # print(f"Decoded text content: {text_content}")
                    # Try to extract JSON
                    try:
                        # Find JSON part
                        json_start = text_content.find('{')
                        json_end = text_content.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = text_content[json_start:json_end]
                            #print(f"Extracted JSON string: {json_str}")
                            return json.loads(json_str)
                        else:
                            # If no JSON format found, return the text content
                            return {"raw_response": text_content}
                    except json.JSONDecodeError:
                        return {"raw_response": text_content}        
        except Exception as e:
            print(f"Image analysis error: {str(e)}")
            return {"error": str(e)}

    def _best_scene(self, reference_image_base64, img_format, width, height, num_imgs, similarity, seed=0):
        """
        Generate a best scene for the product image.
        
        Args:
            product_image (PIL.Image): The product image to be placed on the canvas.
            width (int): The width of the new canvas.
            height (int): The height of the new canvas.
            seed (int): Random seed for reproducibility.
            
        Returns:
            PIL.Image: A new canvas with the product image placed at the target position.
        """
        # get the description of the product image and generate prompt 
        # for generate similar image to the product image
        analysis_result = self._image_analysis(reference_image_base64, img_format=img_format)
        print("Analysis Result:")
        print(json.dumps(analysis_result, indent=2))
        prompt = analysis_result["prompt"] if analysis_result.get("prompt") else "generate a similar image"    
        return self._image_variation(reference_image_base64, prompt, "blur", width, height, num_imgs=num_imgs, similarity_strength=similarity, seed=seed)

    def _multi_scene(self, reference_image_base64, img_format, num_imgs, seed=0):
        analysis_result = self._image_analysis(reference_image_base64, img_format=img_format)
        print("Analysis Result:")
        print(json.dumps(analysis_result, indent=2))
        prompt = analysis_result["prompt"] if analysis_result.get("prompt") else "generate a similar image"
        mask_prompt = analysis_result["product_name"] if analysis_result.get("product_name") else "product"   
        return self._outpaint_with_maskPrompt(reference_image_base64, prompt, mask_prompt, num_imgs=num_imgs, seed=seed, outpainting_mode="PRECISE")
    
    def _brand_gen(self, reference_image_base64, negative_prompt, img_format, width, height, num_imgs, seed=0):
        analysis_result = self._image_analysis(reference_image_base64, img_format=img_format)
        print("Analysis Result:")
        print(json.dumps(analysis_result, indent=2))
        prompt = analysis_result["prompt"] if analysis_result.get("prompt") else "generate a similar image"
        colors = analysis_result["color_list"] if analysis_result.get("color_list") else None
        if negative_prompt is None:
            negative_prompt = 'blur'
        if colors is not None:
            return self._image_color_conditioning(prompt,negative_prompt,width,height,num_imgs,seed)  
        else:
            return self._image_variation(prompt, negative_prompt, width,height, similarity_strength=0.7, seed=seed)


    def _text2video_reel(self, prompt, seed, S3_DESTINATION_BUCKET, durationSeconds=6):
        model_input = {
            "taskType": "MULTI_SHOT_AUTOMATED",
            "multiShotAutomatedParams": {"text": prompt},
            "videoGenerationConfig": {
                "durationSeconds": durationSeconds,  # Must be a multiple of 6 in range [12, 120]
                "fps": 24,
                "dimension": "1280x720",
                "seed": seed,
            },
        }

        invocation = self.bedrock_runtime_client_image.start_async_invoke(
            modelId=self.video_model_id,
            modelInput=model_input,
            outputDataConfig={"s3OutputDataConfig": {"s3Uri": S3_DESTINATION_BUCKET}},
        )

        return invocation

    def _image2video_reel(self, reference_image_base64_list, prompt_list, format_list, seed, S3_DESTINATION_BUCKET):
        video_shot_prompts = []
        # Create a list of video shot prompts
        for i, (image_base64, prompt, img_format) in enumerate(zip(reference_image_base64_list, prompt_list, format_list)):
            video_shot_prompts.append(
                {
                    "text": prompt,
                    "image":{
                        "format": img_format,  # Assuming PNG format for the image
                        "source": {"bytes": image_base64},
                    }
                }
            )
        model_input = {
            "taskType": "MULTI_SHOT_MANUAL",
            "multiShotManualParams": {"shots": video_shot_prompts},
            "videoGenerationConfig": {
                "fps": 24,
                "dimension": "1280x720",
                "seed": seed,
            },
        }
        invocation = self.bedrock_runtime_client_image.start_async_invoke(
                modelId=self.video_model_id,
                modelInput=model_input,
                outputDataConfig={"s3OutputDataConfig": {"s3Uri": S3_DESTINATION_BUCKET}},
            )
        return invocation


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

    def status(self, request):
        if "invocationArn" in request:
            invocation_arn = request["invocationArn"]
            logger.info(f"invocationArn is {invocation_arn}")
            response = self.bedrock_runtime_client_image.get_async_invoke(invocationArn=invocation_arn)
            return response
        else:
            raise ValueError("Invalid request")

    def _transform_request(self, request):
        raise NotImplementedError

    def _transform_response(self, response):
        raise NotImplementedError

    def _get_response(self, response) -> List[str]:
        output = response
        return output
