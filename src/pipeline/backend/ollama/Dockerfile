FROM quay.io/dmaa/ollama:{{VERSION}} AS ollama-base

# Ensure the serve script has executable permissions
# RUN chmod +x /usr/bin/serve
RUN pip install boto3 fastapi uvicorn requests openai modelscope

# Expose port 8080
EXPOSE 8080
WORKDIR /opt/ml/code


# Set the serve script as the entrypoint
ENTRYPOINT ["/usr/bin/serve"]
