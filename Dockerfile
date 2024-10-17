# official Python image from the Docker Hub
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    pkg-config \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the application code
COPY . /app

# Copy the build script and make it executable
COPY build.sh /app/build.sh
RUN chmod +x /app/build.sh

# Run the build script to install dependencies
RUN /app/build.sh

# Collect static files
RUN python /app/manage.py collectstatic --noinput

# Expose the port the app runs on
EXPOSE 8080

# Define environment variable
ENV DEBUG True
ENV MONGODB_HOST mongodb+srv://hseal419:9XsiEbT5jsISKtcP@cluster0.hofar.mongodb.net/murugo-verification-test?retryWrites=true&w=majority
ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV CELERY_TASK_SERIALIZER json
ENV CELERY_RESULT_SERIALIZER json
ENV CELERY_ACCEPT_CONTENT json
ENV CELERY_RESULT_EXPIRES 3600
ENV GEMINI_API_KEY AIzaSyBfOk5t2RSgj88i91zXQLLLrgqN5vh05gw
ENV CLIENT_CALLBACK_URL http://127.0.0.1:8000/api/v2/user/verification/callback

# Run the application using honcho
CMD ["honcho", "start"]