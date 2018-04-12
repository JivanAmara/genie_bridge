FROM phusion/baseimage

ENV PROJECT_DIR=/opt/genie_bridge

# --- Get necessary system packages & set up directories
RUN apt-get update
RUN apt-get install -y python3 python3-pip nginx
RUN rm /etc/nginx/sites-enabled/default
RUN mkdir -p ${PROJECT_DIR}
# Change nginx log file location from /var/log/nginx -> /var/log/genie_bridge
RUN sed -i -- 's/\/var\/log\/nginx/\/var\/log\/genie_bridge/g' /etc/nginx/nginx.conf
RUN mkdir /var/log/genie_bridge

# --- Set up python code
# Problem w/ pip==9.0.2
RUN pip3 install pip==9.0.1
RUN pip3 install gunicorn
COPY . ${PROJECT_DIR}
WORKDIR ${PROJECT_DIR}
ENV PYTHONPATH=${PROJECT_DIR}
RUN pip3 install -r requirements.txt
# Install p4d
RUN cd manual_packages; tar -xvf p4d-1.5.tar.gz; cd p4d-1.5; python3 setup.py install

# --- Prepare initialization scripts to run & services to start on container start
RUN cp docker/nginx/genie_bridge.nginx /etc/nginx/sites-enabled/
RUN cp -r docker/service/* /etc/service/

# -- Build With:
# docker build -t genie_bridge:$(cat docker/version) .

# -- (One time) Generate TLS cert/key
# https://linode.com/docs/security/ssl/create-a-self-signed-tls-certificate/

# --- Run With:
# docker run --name <> -e DB_HOST=<> -p <host_port>:443 -v </host/path/to/tls/dir/>:/opt/tls/ -v </host/path/to/log/dir>:/var/log/genie_bridge/ <image>
