FROM python:3.11-slim

WORKDIR /workspace

# Install dependencies early to utilize Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /workspace/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

