# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app/

# Install dependencies needed for virtualenv (apt-get update is included)
RUN apt-get update && apt-get install -y python3-venv

# Create a virtual environment and install dependencies
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt

# Set environment variable for the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Command to run your application
CMD ["python", "app.py"]
