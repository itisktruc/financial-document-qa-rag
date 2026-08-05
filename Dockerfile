FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
#RUN pip install vietocr
#RUN pip install --upgrade gdown
#RUN python -m venv /opt/venv-paddle
#RUN /opt/venv-paddle/bin/pip install paddleocr==3.7.0 paddlex==3.7.2 numpy==2.3.5 "paddlex[ocr]"
#RUN /opt/venv-paddle/bin/pip install paddlepaddle-gpu==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

COPY ./app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]