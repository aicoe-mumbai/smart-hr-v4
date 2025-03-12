# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables to ensure Python output is sent straight to the terminal (helps with logging)
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for MSSQL ODBC
RUN apt-get update && apt-get install -y \
    gnupg \
    unixodbc \
    unixodbc-dev \
    odbcinst \
    libodbc1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver for SQL Server (For Debian 11 Bullseye)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl -fsSL https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any dependencies required in the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory content
COPY requirements.txt /app/

# Install any dependencies required in the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose the port that Django will run on (default is 8000)
EXPOSE 8000

# Run Django's development server (change it for production use with a WSGI server like Gunicorn)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]