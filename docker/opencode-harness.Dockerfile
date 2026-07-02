FROM node:20-bookworm-slim

ARG OPENCODE_VERSION=1.17.8

RUN npm install -g "opencode-ai@${OPENCODE_VERSION}" \
  && npm cache clean --force \
  && mkdir -p /runner /work /out /task /home/node/.local/share/opencode /home/node/.config/opencode \
  && chown -R node:node /runner /work /out /task /home/node

COPY docker/opencode-runner-entrypoint.sh /runner/opencode-runner-entrypoint.sh

RUN chmod +x /runner/opencode-runner-entrypoint.sh

USER node
ENV HOME=/home/node
ENV NO_COLOR=1
WORKDIR /work

ENTRYPOINT ["/runner/opencode-runner-entrypoint.sh"]
