# Use the official Python image as the base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

# Expose the port where the socket server will listen (use the same port as in the Python script)
EXPOSE 12345

# Command to run the Python script
CMD ["python", "-u", "main.py" ]