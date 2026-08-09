# Home Assistant local add-on image for the waw-calendars pipeline.
# python:slim gives prebuilt lxml wheels (no Alpine build pain); we add git and
# an SSH client for cloning the code and pushing to the `data` branch.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git openssh-client ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV TZ=Europe/Warsaw \
    PIP_NO_CACHE_DIR=1

# Install Python deps at build time from the public repo (fast first run).
# run.sh reconciles them at runtime in case requirements changed upstream.
RUN git clone --depth 1 https://github.com/mik-laj/waw-calendars /tmp/repo \
    && pip install --no-cache-dir -r /tmp/repo/requirements.txt \
    && rm -rf /tmp/repo

COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
