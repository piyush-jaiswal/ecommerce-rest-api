FROM mcr.microsoft.com/devcontainers/python:3-3.12-trixie

ENV PYTHONUNBUFFERED=1

# Install basic development tools and iptables/ipset
RUN apt-get update && apt-get install -y --no-install-recommends \
  less \
  git \
  procps \
  sudo \
  man-db \
  unzip \
  gnupg2 \
  iptables \
  ipset \
  iproute2 \
  dnsutils \
  aggregate \
  jq \
  nano \
  vim \
  iputils-ping \
  postgresql-client \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

ARG USERNAME=vscode

# Persist bash history.
RUN mkdir /commandhistory \
  && touch /commandhistory/.bash_history \
  && chown -R $USERNAME /commandhistory \
  && echo "export PROMPT_COMMAND='history -a'" >> /home/$USERNAME/.bashrc \
  && echo "export HISTFILE=/commandhistory/.bash_history" >> /home/$USERNAME/.bashrc

# Set `DEVCONTAINER` environment variable to help with orientation
ENV DEVCONTAINER=true

RUN mkdir -p /workspace && \
  chown -R $USERNAME:$USERNAME /workspace

WORKDIR /workspace

# Set up non-root user
USER $USERNAME

# Set the default editor and visual
ENV EDITOR=nano
ENV VISUAL=nano

# [Optional] If your requirements rarely change, uncomment this section to add them to the image.
RUN mkdir /home/$USERNAME/pip-tmp
COPY requirements-base.txt requirements-dev.txt requirements-test.txt /home/$USERNAME/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install --user \
  -r /home/$USERNAME/pip-tmp/requirements-dev.txt \
  -r /home/$USERNAME/pip-tmp/requirements-test.txt \
  && rm -rf /home/$USERNAME/pip-tmp

# Copy and set up firewall script
USER root
COPY .devcontainer/init-firewall.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/init-firewall.sh
USER $USERNAME
