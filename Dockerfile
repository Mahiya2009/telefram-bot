# Use an official Python runtime as a parent image
FROM python:3.9

# Set environment variables (optional)
ENV NIXPACKS_PATH=/opt/venv/bin:$NIXPACKS_PATH

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app/.

# Install dependencies
RUN apt-get update && apt-get install -y python3-venv

# Create and activate a virtual environment, then install dependencies
RUN python3 -m venv --copies /opt/venv && . /opt/venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

# Set environment variable for the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Command to run your application
CMD ["python", "app.py"]
