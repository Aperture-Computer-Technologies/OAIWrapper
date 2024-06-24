FROM python:3.12.4

# Create the application user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 -ms /bin/bash appuser

# Upgrade pip and install virtualenv
RUN pip3 install --no-cache-dir --upgrade \
    pip \
    virtualenv

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    git

USER appuser
WORKDIR /home/appuser

# Clone the repository as appuser
RUN git clone https://github.com/Aperture-Computer-Technologies/Synapse app

# Create and activate a virtual environment, then install dependencies
ENV VIRTUAL_ENV=/home/appuser/venv
RUN virtualenv ${VIRTUAL_ENV}
RUN . ${VIRTUAL_ENV}/bin/activate && pip install -r app/requirements.txt

EXPOSE 8501

# Switch back to root to set permissions on the run.sh script
USER root
COPY run.sh /home/appuser
RUN chmod +x /home/appuser/run.sh

# Switch back to appuser
USER appuser

ENTRYPOINT ["./run.sh"]
