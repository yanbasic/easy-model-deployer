cd src/pipeline
export model_id=Qwen2.5-0.5B-Instruct
export model_tag=latest
python pipeline.py \
    --model_id txt2video-LTX \
    --model_tag latest \
    --model_s3_bucket "emd-test-3" \
    --backend_type comfyui \
    --service_type local \
    --instance_type g5.4xlarge \
    --region us-west-2 \
    --framework_type fastapi \
    --role_name SageMakerExecutionRoleTest6 \
    --disable_parallel_prepare_and_build_image