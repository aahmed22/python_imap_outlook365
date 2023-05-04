# Most of the time, Alpine is a great base image to start with.
# If we're building a container for Python, we use something different.
# Learn why here: https://pythonspeed.com/articles/base-image-python-docker-images/
# TLDR: Alpine is very slow when it comes to running Python!

# STEP 1: Install base image. Optimized for Python.
#FROM python:3.8-slim-buster
FROM --platform=linux/amd64 python:3.8-slim-buster
# install FreeTDS and dependencies
RUN apt-get update \
 && apt-get install unixodbc -y \
 && apt-get install unixodbc-dev -y \
 && apt-get install freetds-dev -y \
 && apt-get install freetds-bin -y \
 && apt-get install tdsodbc -y \
 && apt-get install --reinstall build-essential -y \
 && apt-get -y install libpq-dev gcc \
 && pip install psycopg2

# Install dependencies for sql server drivers
RUN apt-get update \
    && apt-get install -y curl apt-transport-https \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev 


# STEP 3: Copy the source code in the current directory to the container.
# Store it in a folder named /app.
ADD . /

# STEP 4: Set working directory to /app so we can execute commands in it
WORKDIR /


# Install the rest of the requirements
RUN pip install -r requirements.txt


CMD [ "python3", "./main.py"]
