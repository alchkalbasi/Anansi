FROM alpine:latest
RUN apk add --no-cache \
      bash \
      git \
      openssh \
      curl \
      make \
      tar \
      gzip \
      unzip \ 
      coreutils \
      openssl \
      grep \
      && rm -rf /var/cache/apk

# set bash as default
SHELL ["/bin/bash", "-c"]