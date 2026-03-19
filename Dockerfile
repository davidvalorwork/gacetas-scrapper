# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Set the working directory in the container
WORKDIR /app


# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
# Adding gunicorn for a production-ready WSGI server
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the application's source code
COPY . .

ENV MONGO_URI=mongodb://34.46.169.192/27017

# Expose port 80 for the app
EXPOSE 80

# Command to run the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "3", "--timeout", "120", "app:app"]
