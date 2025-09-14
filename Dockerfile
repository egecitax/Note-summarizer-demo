FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DATABASE_URL=sqlite:///./app.db
ENV JWT_SECRET=supersecret
ENV USE_HF=false
ENV HF_MODEL=sshleifer/tiny-distilbart-cnn-6-6
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
