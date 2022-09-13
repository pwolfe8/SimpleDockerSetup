#!/bin/bash

echo ""
echo "running host docker setup script"
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

    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null


    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
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
