# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app/

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    python3-venv \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && apt-get clean

# Create a virtual environment
RUN python3 -m venv /opt/venv

# Upgrade pip in the virtual environment
RUN /opt/venv/bin/pip install --upgrade pip

# Install requirements
RUN /opt/venv/bin/pip install -r requirements.txt

# Set environment variable for the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Command to run your application
CMD ["python", "app.py"]
