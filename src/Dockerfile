# 1. Base image
FROM python:3.11-slim

# 2. Set workdir inside container
WORKDIR /app

# 3. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy application code
COPY .. .

# 5. Expose the port your server listens on
EXPOSE 9000

# 6. Launch the HTTP server on container start
CMD ["python", "server_http.py"]
