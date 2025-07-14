FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /

RUN apt-get update && apt-get install -y \
    git \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

RUN pip install runpod

ENV MODEL_ID="runwayml/stable-diffusion-v1-5"
RUN python -c "from diffusers import StableDiffusionPipeline; import torch; StableDiffusionPipeline.from_pretrained('${MODEL_ID}', torch_dtype=torch.float16)"

COPY src/ /src/

CMD ["python", "-u", "/src/handler.py"]