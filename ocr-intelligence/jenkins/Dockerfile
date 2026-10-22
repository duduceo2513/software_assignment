# Jenkins with everything the OCR Intelligence pipeline needs: Python (tests) and Docker CLI (image builds).
FROM jenkins/jenkins:lts-jdk17

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv python3-pip docker-cli \
    && rm -rf /var/lib/apt/lists/*
# Root is needed to talk to the host Docker socket mounted by docker-compose.jenkins.yml.
# Local/learning setup only.
