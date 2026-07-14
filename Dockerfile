FROM debian:stable-slim

ARG TARGETPLATFORM

COPY ./dist/${TARGETPLATFORM}/maws /usr/bin/maws

ENTRYPOINT ["maws"]
