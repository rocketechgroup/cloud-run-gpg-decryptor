# Use the official Python 3.8 image as the base image
FROM python:3.8-slim

ARG APP_HOME=/home/app

# Install GnuPG and required dependencies
RUN apt-get update && apt-get install -y gnupg

# Add user
RUN groupadd -g 999 app && useradd -r -u 999 -g app app

# Create and set the working directory
WORKDIR ${APP_HOME}

# create the gnupg directory
RUN mkdir ${APP_HOME}/.gnupg && chmod 700 ${APP_HOME}/.gnupg

# change permission to app user
RUN chown -R app:app ${APP_HOME}

# change to app user
USER app

# Copy requirements.txt and install the required Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY decryptor.py .
COPY file_to_encrypt.txt .
COPY private.pgp .
COPY public.pgp .

# Expose the port for the application to run on
EXPOSE 8080

# Define the command to run the application
CMD ["python", "decryptor.py"]