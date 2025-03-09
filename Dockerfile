RUN apt-get update && apt-get install -y \
    libssl-dev \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Use the official Python 3.9 image as the base image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Install system dependencies required by some Python packages (e.g., python-telegram-bot)
RUN apt-get update && apt-get install -y \
    libssl-dev \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app/

# Set up a virtual environment in /opt/venv
RUN python3 -m venv /opt/venv

# Upgrade pip in the virtual environment
RUN /opt/venv/bin/pip install --upgrade pip

# Install the dependencies from requirements.txt using the virtual environment's pip
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Make sure Python packages installed in the virtual environment can be accessed
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port that the application will run on (if needed)
EXPOSE 8080

# Define the command to run your application (e.g., bot.py)
CMD ["/opt/venv/bin/python", "your_script.py"]
