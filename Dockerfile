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

# Expose port 5000 for the app
EXPOSE 5000

# Command to run the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--timeout", "120", "app:app"]
