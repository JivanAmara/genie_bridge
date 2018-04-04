FROM phusion/baseimage

ENV PROJECT_DIR=/opt/genie_bridge

# --- Get necessary system packages & set up directories
RUN apt-get update
RUN apt-get install -y python3 python3-pip nginx
RUN rm /etc/nginx/sites-enabled/default
RUN mkdir -p ${PROJECT_DIR}
RUN touch /var/log/gunicorn_genie_bridge.log
RUN chmod a+rw /var/log/gunicorn_genie_bridge.log

# --- Set up python code
# Problem w/ pip==9.0.2
RUN pip3 install pip==9.0.1
RUN pip3 install gunicorn
COPY . ${PROJECT_DIR}
WORKDIR ${PROJECT_DIR}
ENV PYTHONPATH=${PROJECT_DIR}
RUN pip3 install -r requirements.txt

# --- Prepare initialization scripts to run & services to start on container start
RUN cp docker/nginx/genie_bridge.nginx /etc/nginx/sites-enabled/
RUN cp -r docker/service/* /etc/service/

# -- Build With:
# docker build -t genie_bridge:$(cat docker/version) .

# --- Run With:
# docker run --name <> -p <host_port>:443 -v </host/path/to/tls/dir/>:/opt/tls/ -v </host/path/do/log/dir>:/var/log <image>
