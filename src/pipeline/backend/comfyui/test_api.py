import json
import random
import uuid
import os
import io
import sys
import base64

from urllib import request, parse
from PIL import Image
import websocket

#This is the ComfyUI api prompt format.

#If you want it for a specific workflow you can "enable dev mode options"
#in the settings of the UI (gear beside the "Queue Size: ") this will enable
#a button on the UI to save workflows in api format.

#keep in mind ComfyUI is pre alpha software so this format will change a bit.
#this is the one for the default workflow

def track_progress(prompt, ws, prompt_id):
  node_ids = list(prompt.keys())
  finished_nodes = []

  while True:
      out = ws.recv()
      if isinstance(out, str):
          message = json.loads(out)
          print('!!!!!!!!', message['type'])
          if message['type'] == 'progress':
              data = message['data']
              current_step = data['value']
              print('In K-Sampler -> Step: ', current_step, ' of: ', data['max'])
          if message['type'] == 'execution_cached':
              data = message['data']
              for itm in data['nodes']:
                  if itm not in finished_nodes:
                      finished_nodes.append(itm)
                      print('Progess: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')
          if message['type'] == 'executing':
              data = message['data']
              if data['node'] not in finished_nodes:
                  finished_nodes.append(data['node'])
                  print('Progess: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')

              if data['node'] is None and data['prompt_id'] == prompt_id:
                  break #Execution is done
      else:
          continue
  return

def show_gif(fname):
    from IPython import display
    with open(fname, 'rb') as fd:
        b64 = base64.b64encode(fd.read()).decode('ascii')
    return display.HTML(f'<img src="data:image/gif;base64,{b64}" />')

def open_websocket_connection(base_url):
  client_id=str(uuid.uuid4())
  ws = websocket.WebSocket()
  ws.connect(f"ws://{base_url}/ws?clientId={client_id}")
  return ws, client_id

def get_history(prompt_id, base_url):
  with request.urlopen(f"http://{base_url}/history/{prompt_id}") as response:
      data = json.loads(response.read())
      return data

def get_image(filename, subfolder, folder_type, server_address):
  data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
  url_values = parse.urlencode(data)
  with request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
      return response.read()

def get_images(prompt_id, server_address):
  output_images = {}
  history = get_history(prompt_id, server_address)[prompt_id]
  for node_id in history['outputs']:
      node_output = history['outputs'][node_id]
      print(node_id, node_output)
      if 'images' in node_output:
          images_output = []
          for image in node_output['images']:
              image_data = get_image(image['filename'], image['subfolder'], image['type'], server_address)
              images_output.append(image_data)
          output_images[node_id] = images_output
      if 'videos' in node_output:
          videos_output = []
          for video in node_output['videos']:
              video_data = get_image(video['filename'], video['subfolder'], video['type'], server_address)
              videos_output.append(video_data)
          output_images[node_id] = videos_output
      if 'gifs' in node_output:
          gifs_output = []
          for gif in node_output['gifs']:
              gif_data = get_image(gif['filename'], gif['subfolder'], gif['type'], server_address)
              gifs_output.append(gif_data)
          output_images[node_id] = gifs_output
  #print(output_images)
  return output_images

def save_image(images, output_path, save_previews):
  for node_id in images:
    for image_data in images[node_id]:
      itm = json.loads(image_data)
      directory = os.path.join(output_path, 'temp/') if itm['type'] == 'temp' and save_previews else output_path
      os.makedirs(directory, exist_ok=True)
      try:
          image = Image.open(io.BytesIO(itm['image_data']))
          image.save(os.path.join(directory, itm['file_name']))
      except Exception as e:
          print(f"Failed to save image {itm['file_name']}: {e}")

def queue_prompt(prompt, client_id, server_address):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    req =  request.Request("http://{}/prompt".format(server_address), data=data, headers=headers)
    return json.loads(request.urlopen(req).read())
    #request.urlopen(req)

def invoke(request_body, server_address):
    data = json.dumps(request_body).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    req =  request.Request("http://{}/invocations".format(server_address), data=data, headers=headers)
    return json.loads(request.urlopen(req).read())

def invoke_sam(workflow_path, server_address):
    with open('./product.png', "rb") as f:
        input_image_bytes = f.read()
        input_image_base64 = base64.b64encode(input_image_bytes).decode("utf-8")
    
    f = open(workflow_path, 'r')
    prompt = json.load(f)
    prompt['16']['inputs']['prompt'] = 'sofa'
    prompt['16']['inputs']['threshold'] = 0.3
    prompt['47']['inputs']['base64_data'] = input_image_base64

    prompt_new = {"prompt": prompt, "client_id": str(uuid.uuid4())}
    workflow_request = {
        "taskType": "WORKFLOW",
        "workflow": prompt_new
    }
    response = invoke(workflow_request, server_address)
    print(response['images'].keys())
    return response

def invoke_product_replace(workflow_path, server_address):
    f = open(workflow_path, 'r')
    prompt = json.load(f)
    with open('./logo.png', "rb") as f:
        input_image_bytes = f.read()
        input_image_base64 = base64.b64encode(input_image_bytes).decode("utf-8")
    prompt['204']['inputs']['base64_data'] = input_image_base64
    
    with open('./bus_alpha.png', "rb") as f:
        input_image_bytes = f.read()
        input_image_base64 = base64.b64encode(input_image_bytes).decode("utf-8")
    prompt['203']['inputs']['base64_data'] = input_image_base64

    prompt_new = {"prompt": prompt, "client_id": str(uuid.uuid4())}
    workflow_request = {
        "taskType": "WORKFLOW",
        "workflow": prompt_new
    }
    response = invoke(workflow_request, server_address)
    print(response['images'].keys())
    return response

def invoke_image_edit(workflow_path, server_address):
    f = open(workflow_path, 'r')
    prompt = json.load(f)
    with open('./girl_test.png', "rb") as f:
        input_image_bytes = f.read()
        input_image_base64 = base64.b64encode(input_image_bytes).decode("utf-8")
    prompt['72']['inputs']['base64_data'] = input_image_base64
    prompt['1']['inputs']['editText'] = 'wearing a sun glasses with a red frame and brown lenses'

    prompt_new = {"prompt": prompt, "client_id": str(uuid.uuid4())}
    workflow_request = {
        "taskType": "WORKFLOW",
        "workflow": prompt_new
    }
    response = invoke(workflow_request, server_address)
    print(response['images'].keys())
    return response

def invoke_super_resolution(workflow_path, server_address):
    f = open(workflow_path, 'r')
    prompt = json.load(f)
    with open('./6.png', "rb") as f:
        input_image_bytes = f.read()
        input_image_base64 = base64.b64encode(input_image_bytes).decode("utf-8")
    prompt['8']['inputs']['base64_data'] = input_image_base64
    prompt['5']['inputs']['upscale_ratio'] = 2
    prompt_new = {"prompt": prompt, "client_id": str(uuid.uuid4())}
    workflow_request = {
        "taskType": "WORKFLOW",
        "workflow": prompt_new
    }
    response = invoke(workflow_request, server_address)
    print(response['images'].keys())
    return response

if __name__ == "__main__":
    
    workflow_path = sys.argv[1]
    http_base_url = sys.argv[2]

    encoded_image = base64.b64encode(open("test_car.png", "rb").read()).decode("utf-8")
    #### remove background
    remove_background_request = {
        "taskType": "BACKGROUND_REMOVAL",
        "backgroundRemovalParams": {"image": encoded_image}
    }
    #### text to image
    text_to_image_request = {
        "taskType": "TEXT_TO_IMAGE",
        "textToImageParams": {
                "text": "car on the beach",  # Text prompt to guide the generation
                "negativeText": "blur",
            },  # What to avoid generating inside the image
            "imageGenerationConfig": {
            "numberOfImages": 2,  # Number of images to generate, up to 5
            "width": 1024,
            "height": 1024,
            "cfgScale": 6.5,  # How closely the prompt will be followed
            "seed": 1111111,  # Any number from 0 through 858,993,459
            }
    }
    #### image varation
    image_variation_request = {
        "taskType": "IMAGE_VARIATION",
        "imageVariationParams": 
        {
                    "text": "a red car running on the road",
                    "negativeText": "blur",  # What to avoid generating inside the image
                    "images": [
                        encoded_image
                    ],  # May provide up to 5 reference images here
                    "similarityStrength": 0.6,  # How strongly the input images influence the output. From 0.2 through 1.
                },
                "imageGenerationConfig": {
                    "numberOfImages": 2,  # Number of images to generate, up to 5.
                    "seed": 11111,  # Any number from 0 through 858,993,459
                    "width": 1024,
                    "height": 1024,
                }
    }
    #### color_guided_image_generation
    colors = ["#FFFFFF", "#FF9900", "#F2F2F2", "#232F3E"]
    color_guided_image_generation_request = {
        "taskType": "COLOR_GUIDED_GENERATION",
        "colorGuidedGenerationParams": 
        {
                "text": "a red car running on the road",
                "negativeText": "blur",  # What to avoid generating inside the image
                "colors": colors,
            },
            "imageGenerationConfig": {
                "numberOfImages": 2,  # Number of images to generate, up to 5
                "width": 1024,
                "height": 1024,
            }
    }
    #### outpaint
    outpaint_request = {
        "taskType": "OUTPAINTING",
        "outPaintingParams":
        {
                "text": "beach and sea rocky shore",  # Text prompt to guide the generation
                "negativeText": "blur",  # What to avoid generating inside the image
                "image": encoded_image,  # May provide up to 5 reference images here
                "maskPrompt": "car",
            },
            "imageGenerationConfig": {
                "numberOfImages": 2,  # Number of images to generate, up to 5.
                "seed": 11111,  # Any number from 0 through 858,993,459
            }
    }
    #### inpaint
    replace_object_request = {
        "taskType": "REPLACE_OBJECT",
        "inPaintingParams":
        {
                "text": "jeep",
                "negativeText": "blur",  # What to avoid generating inside the image
                "image": encoded_image,  # May provide up to 5 reference images here
                "maskPrompt": "car",
            },
            "imageGenerationConfig": {
                "numberOfImages": 2,  # Number of images to generate, up to 5.
                "seed": 11111,  # Any number from 0 through 858,993,459
            }
    }
    #### remove object
    remove_object_request = {
        "taskType": "REMOVE_OBJECT",
        "inPaintingParams":
        {
                "text": "jeep",
                "negativeText": "blur",  # What to avoid generating inside the image
                "image": encoded_image,  # May provide up to 5 reference images here
                "maskPrompt": "car",
            },
            "imageGenerationConfig": {
                "numberOfImages": 2,  # Number of images to generate, up to 5.
                "seed": 11111,  # Any number from 0 through 858,993,459
            }
    }  

    #response = invoke(remove_background_request, http_base_url)
    #response = invoke(text_to_image_request, http_base_url)
    #response = invoke(image_variation_request, http_base_url)
    #response = invoke(color_guided_image_generation_request, http_base_url)
    #response = invoke(replace_object_request, http_base_url)
    #response = invoke(remove_object_request, http_base_url)
    #response = invoke(outpaint_request, http_base_url)
    #response = invoke_super_resolution(workflow_path, http_base_url)
    response = invoke_image_edit(workflow_path, http_base_url)
    #response = invoke_product_replace(workflow_path, http_base_url)
    #response = invoke_sam(workflow_path, http_base_url)

    print("Response keys:", response.keys())
    base64_images = response.get("images")
    if isinstance(base64_images, dict):
        for key in base64_images.keys():
            print("Response images:", key)
            response_image = Image.open(io.BytesIO(base64.b64decode(base64_images[key])))
            # save the response_images to a file
            response_image.save(f"{key}")
    else:
        print("Response images:", len(base64_images))
        response_images = [
            Image.open(io.BytesIO(base64.b64decode(base64_image)))
            for base64_image in base64_images
        ]
        # save the response_images to a file
        for i, img in enumerate(response_images):
            task_type = outpaint_request.get("taskType")
            img.save(f"src/pipeline/backend/comfyui/test_car_text_to_{task_type}_{i}.png")