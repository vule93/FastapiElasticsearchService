# Dockerfile

# pull the official docker image
FROM python:3.9.6

# set work directory
WORKDIR /app

# install dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# copy project
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008"]