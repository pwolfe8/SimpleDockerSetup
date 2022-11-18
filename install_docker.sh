#!/bin/bash

DISTRO=${1:-"ubuntu"}
if [ $DISTRO == "debian" ] ; then
  echo "you may want to run rpi-update first"
  echo "press enter to continue or ctrl+c to back out"
  read user_continue
fi

echo ""
echo "running host docker setup script for distro choice: $DISTRO (default ubuntu)"
echo ""

if [ -x "$(command -v docker)" ]; then
    echo "docker is already installed"
else
    echo "docker is not installed. setting up now"
    
    sudo apt update && sudo apt install -y \
      ca-certificates \
      curl \
      gnupg \
      lsb-release
    
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/${DISTRO}/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${DISTRO} \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null


    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

GROUP=docker
if [ "$(groups | grep -c $GROUP)" -ge 1 ]; then
  echo $USER already belongs to group $GROUP
else
  echo "$USER does not belong to $GROUP. adding now"
  sudo usermod -aG docker ${USER}
  su - ${USER}  
fi

echo ""
echo "done"
echo ""
