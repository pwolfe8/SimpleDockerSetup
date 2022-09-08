ARG FROM_IMG
FROM ${FROM_IMG}

# update pip and install requirements.txt
COPY requirements.txt /root/requirements.txt
RUN cd /root && pip3 install --upgrade pip && pip3 --version
RUN cd /root && pip3 install -r requirements.txt && rm requirements.txt

# make this match your docker compose yaml working_dir 
ARG WORKING_DIR=/root/${BASENAME}

# copy in starting command
COPY ./ContainerCode/entrypoint.sh ${WORKING_DIR}
