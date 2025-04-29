
To build the current image, please first download the following repo:
```shell
git clone  https://github.com/vllm-project/vllm.git vllm_glm_z1
cd vllm_glm_z1 && git reset --hard fe742aef5aaf406c62cafa248068818bfe517d6e
```
Then run the following command to build the image:
```shell
#optionally specifies: --build-arg max_jobs=8 --build-arg nvcc_threads=2
DOCKER_BUILDKIT=1 docker build --build-arg max_jobs=8 --build-arg nvcc_threads=2 -f docker/Dockerfile . --target vllm-openai --tag vllm/vllm-openai:glm_z1_and_0414
docker tag vllm/vllm-openai:glm_z1_and_0414 public.ecr.aws/aws-gcr-solutions/dmaa-vllm/vllm-openai:glm_z1_and_0414
```
