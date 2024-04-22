FROM ubuntu:22.04

RUN apt update && apt upgrade -y
RUN apt install vim python3 python3-pip postgresql-server-dev-all -y
COPY ./requirements.txt /
RUN pip3 install -r requirements.txt

COPY ./api /app/api
COPY ./database /app/database
COPY ./user_service.py /app/user_service.py
COPY ./utils.py /app/utils.py
WORKDIR /app

ENTRYPOINT ["python3", "user_service.py"]