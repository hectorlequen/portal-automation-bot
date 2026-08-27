FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY demo_portal_data ./demo_portal_data

EXPOSE 5000

CMD ["python", "app.py"]
