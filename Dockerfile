# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Make port 1883 available to the world outside this container (if needed for MQTT)
EXPOSE 1883

# Run the Python script when the container launches
CMD ["python", "./wol_service.py"]
