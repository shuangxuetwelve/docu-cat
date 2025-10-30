FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone dataset repository
RUN mkdir -p /home/datasets && \
    git clone https://github.com/shuangxuetwelve/docu-cat-dataset-next-js.git /home/datasets/docu-cat-dataset-next-js

WORKDIR /home/datasets/docu-cat-dataset-next-js
RUN git checkout -b test-case-rename origin/test-case-rename

# Set working directory
WORKDIR /home/docu-cat

# Copy all files (respecting .dockerignore)
COPY . /home/docu-cat/

# Install dependencies
RUN uv sync
