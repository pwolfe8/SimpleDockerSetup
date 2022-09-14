# Uncomment to use one of my images
# ARG FROM_IMG
# FROM ${FROM_IMG}

### Otherwise use your desired FROM image
FROM ubuntu:22.04

# install python3 and pip and update pip and install requirements.txt
RUN apt update && apt install -y python3 python3-pip && pip3 install --upgrade pip && pip3 --version
COPY requirements.txt /root/requirements.txt
RUN cd /root && pip3 install -r requirements.txt && rm requirements.txt


# COPY ./${CONTAINER_FOLDER}/entrypoint.sh ${}
