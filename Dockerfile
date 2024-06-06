FROM python:3.10-slim as llamacpp-server

RUN apt-get update && \
    apt-get install -y libgomp1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

#RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

ENTRYPOINT ["python", "main.py", "--config_file", "/app/configs/config_llamacpp_docker.json"]
