# Dedicated OpenClaw runtime; separate from the Streamlit Railway service.
FROM node:26-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates gosu \
  && rm -rf /var/lib/apt/lists/*
RUN npm install -g openclaw@latest && openclaw --version
WORKDIR /opt/marketing-openclaw-ai
COPY . /opt/marketing-openclaw-ai/
COPY deploy/railway-agent/start.sh /usr/local/bin/start-marketing-agent
RUN chmod 755 /usr/local/bin/start-marketing-agent
ENV OPENCLAW_STATE_DIR=/data/.openclaw \
    OPENCLAW_WORKSPACE_DIR=/data/workspace \
    HOME=/home/node
EXPOSE 8080
CMD ["/usr/local/bin/start-marketing-agent"]
