cd src/pipeline
python -m deploy.deploy_on_codebuild.pipeline \
    --model_id whisper \
    --backend_type huggingface \
    --service sagemaker \
    --instance_type g5.2xlarge \
    --region us-west-2 \
    --is_async_deploy false \
    --framework_type fastapi \
