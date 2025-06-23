import json
import random
import uuid
import os
import io
import sys
import base64
import requests
import boto3
import logging
from botocore.config import Config


from urllib import request, parse
from PIL import Image
import websocket

def convertImageToPngBase64(image):
    """
    Converts an image to PNG format and returns the base64-encoded
    representation of that PNG.
    """
    mem_file = io.BytesIO()
    image.save(mem_file, format="PNG")
    mem_file.seek(0)
    png_bytes = mem_file.read()

    return base64.b64encode(png_bytes).decode("utf-8")


bedrock_runtime_client = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    config=Config(
        read_timeout=5 * 60
    ),  # IMPORTANT: Increase the read timeout to 5 minutes to support longer operations.
)
image_generation_model_id = "amazon.nova-canvas-v1:0"



image_path = 'test6.png'
target_aspect_ratio = 3/2

def resize_canvas(image_path, target_aspect_ratio):

    original_image = Image.open(image_path)
    width, height = original_image.size
    target_width = int(height * target_aspect_ratio)

    if width == target_width:
        response_body = {
                    "status": "success",
                    "images": [base64.b64encode(open(image_path, "rb").read()).decode("utf-8")],
                }
        response =  response_body  # No expansion needed
    else:
        if width > target_width:
            # If the image is wider than the target aspect ratio,
            # expand the height to match the target aspect ratio
            target_height = int(width / target_aspect_ratio)
            target_width = width
            top = (target_height - height) // 2
            position = (0, top)
        else:
            target_width = int(height * target_aspect_ratio)
            target_height = height
            left = (target_width - width) // 2
            position = (left, 0)

        WHITE = (255, 255, 255)
        BLACK = (0, 0, 0)
        input_image = Image.new("RGB", (target_width, target_height), (230, 230, 230))
        input_image.paste(original_image, position)
        input_image.save('expand_image1.png')
        expanded_image_base64 = convertImageToPngBase64(input_image)

        # Create mask that matches the canvas size and masks the place where the
        # original image is positioned.
        mask_image = Image.new("RGB", (target_width, target_height), WHITE)
        original_image_shape = Image.new("RGB", (width, height), BLACK)
        mask_image.paste(original_image_shape, position)
        mask_image.save('mask.png')
        mask_image_base64 = convertImageToPngBase64(mask_image)
    
    return expanded_image_base64, mask_image_base64


expanded_image_base64, mask_image_base64 = resize_canvas(image_path, target_aspect_ratio)

#prompt = "A modern, minimalist over-sink dish rack with a sleek white metal frame and a frosted ribbed sliding glass door. The rack is mounted above a white sink and countertop, designed for convenient dish drying and storage. Behind the rack is a large window with white horizontal blinds, letting in soft natural light. The faucet has a clean, contemporary design with dual handles, complementing the stylish and functional kitchen setup."
#prompt = "A modern dark gray fabric armchair with a minimalist design, black metal armrests, and sturdy legs, placed in a cozy corner of a bright room. Behind the chair is a large window with soft daylight illuminating the space. A green potted plant sits beside the chair. The floor features a contemporary area rug with abstract orange and black shapes on a light-colored background. The room has a clean, Scandinavian-inspired aesthetic."
#prompt = "The image shows a modern office chair with a white base and a grey seat. The chair has a high backrest and armrests, and a footrest on the right side. The seat is upholstered in a light grey fabric with a textured pattern. On the left side of the chair, there is a yellow label with Chinese text. The chair also has four wheels for easy movement. The background is white, and there are six smaller images on the image, each showing a different angle of the seat."
#prompt = "The image shows a wooden kitchen cabinet with a built-in shelf and two drawers. The cabinet is made of light-colored wood and has a sleek and modern design. The top shelf has multiple compartments for storing kitchen items such as bottles, jars, and other kitchen utensils. The bottom shelf has three drawers for storage. The cabinets are placed against a white wall with a wooden floor and a potted plant on the right side. The overall aesthetic of the cabinet is minimalistic and contemporary."
#prompt = "The image shows three bottles of eco-bix mouthwash on a blue background with water droplets. The bottles are arranged in a triangular formation, with the largest bottle in the center and two smaller bottles on either side. All three bottles have a white cap and a blue label with the brand name 'ecobix' written in Chinese. The label also has a small illustration of a yellow ball on top. The background is a gradient of blue and white, with a hint of purple. The image appears to be an advertisement for the product."
#prompt = "The image shows a tall, cylindrical bottle with a gold-colored cap. The bottle is placed on a bed of green moss, with a small seashell resting on the edge. The background is a dark green color, and there are a few palm leaves scattered around the bottle. The overall mood of the image is peaceful and serene."
#prompt = "The image is a digital illustration of a three-tiered wedding cake. The cake is white and has a round base. On top of the cake, there are two white lilies with long, pointed petals and green leaves. The lilies are arranged in a symmetrical manner, with one on the left side and the other on the right side. The background is a light beige color with a subtle wave-like design on the top right corner. The overall style of the illustration is elegant and romantic."
prompt = "The image is a flat lay of a pink background with a white bottle of Taime skincare product in the center. The bottle has a pump dispenser and a label with the brand name 'Taime' written in a cursive font. Surrounding the bottle are several pink and white peonies with green leaves. The peonies are arranged in a scattered manner, with some overlapping each other. The overall aesthetic of the image is soft and delicate."
body = json.dumps(
        {
        "taskType": "OUTPAINTING",
        "outPaintingParams": {
            "text": prompt,  # The text prompt to guide the image generation
            "negativeText": "blur, watermark",  # What to avoid generating inside the mask
            "image": expanded_image_base64,  # The image to edit
            "maskImage": mask_image_base64,  # One of "maskImage" or "maskPrompt" is required
            "outPaintingMode": "DEFAULT",  # Either "DEFAULT" or "PRECISE"
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,  # Number of images to generate, up to 5.
            "cfgScale": 6.5,  # How closely the prompt will be followed
            "seed": 12,  # Any number from 0 through 858,993,459
            "quality": "standard",  # Either "standard" or "premium". Defaults to "standard".
        },
    }
    )

print("Generating image...")
response = bedrock_runtime_client.invoke_model(
    body=body,
    modelId=image_generation_model_id,
    accept="application/json",
    contentType="application/json",
)
response_body = json.loads(response.get("body").read())
base64_images = response_body.get("images")

response_images = [
    Image.open(io.BytesIO(base64.b64decode(base64_image)))
    for base64_image in base64_images
]
# save the response_images to a file
for i, img in enumerate(response_images):
    task_type = "outpaint"
    img.save(f"{image_path.split('.')[0]}_{task_type}_{i}.png")
