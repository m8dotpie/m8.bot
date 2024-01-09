# Use the official Python image as the base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

# Command to run the Python script
CMD ["python", "-u", "restarter.py", ";", "python", "-u", "main.py" ]