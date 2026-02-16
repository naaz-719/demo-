# Use the Python version found in your MLmodel file
FROM python:3.13-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API code and the model artifacts
COPY . .

# Expose the port your Flask app uses
EXPOSE 5000

# Command to run the API
CMD ["python", "app.py"]