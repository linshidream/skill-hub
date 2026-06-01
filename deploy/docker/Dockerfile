FROM alpine:3.20

ARG RELEASE_DIR=dist/releases/latest

LABEL org.opencontainers.image.title="skill-hub"
LABEL org.opencontainers.image.description="Deployable Agent skill directory"

WORKDIR /opt/skill-hub/current
COPY ${RELEASE_DIR}/ /opt/skill-hub/current/

CMD ["sh", "-c", "find /opt/skill-hub/current/skills -name SKILL.md -print && sleep infinity"]
