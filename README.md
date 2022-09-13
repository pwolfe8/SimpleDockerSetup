# SimpleDockerSetup

DISCLAIMER: Made on a Linux host. may / may not work with WSL 2 on Windows. Haven't tested yet

## Setup Docker

Run `./install_docker.sh` may need to type in your sudo password

## Container Commands

I made a container helper script called `container.py`.

Run `./container.py -h` for full list of commands.

Here are commands you can do:

```bash
# builds container image using Dockerfile and brings up container with settings chosen in docker-compose.yaml 
./container.py up 

# attaches bash session to container 
./container.py attach

# restarts container
./container.py restart

# brings down container
./container.py restart

# checks container status
./container.py status

# checks container command output 
./container.py logs

```
