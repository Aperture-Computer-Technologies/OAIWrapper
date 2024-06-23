FROM python:3.12.4

# Upgrade pip and install virtualenv
RUN pip3 install --no-cache-dir --upgrade \
    pip \
    virtualenv

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    git

WORKDIR /root

# Clone the repository as root
RUN git clone https://github.com/Aperture-Computer-Technologies/OAIWrapper app

# Create and activate a virtual environment, then install dependencies
ENV VIRTUAL_ENV=/root/venv
RUN virtualenv ${VIRTUAL_ENV}
RUN . ${VIRTUAL_ENV}/bin/activate && pip install -r app/requirements.txt

EXPOSE 8501

# Copy and set permissions on the run.sh script
COPY run.sh /root
RUN chmod +x /root/run.sh

ENTRYPOINT ["./run.sh"]