FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONBUFFERES=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
