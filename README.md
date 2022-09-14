# SimpleDockerSetup

DISCLAIMER: Made on a Linux host. may / may not work with WSL 2 on Windows. Haven't tested yet

## Setup Docker

Run `./install_docker.sh` may need to type in your sudo password

## Container Commands

I made a container helper script called `container.py`.

Run `./container.py -h` for full list of commands.

Here are commands you can do for the whole project (all containers):

```bash
# builds container image using Dockerfile and brings up container with settings chosen in docker-compose.yaml 
./container.py up 

# restarts container
./container.py restart

# brings down container
./container.py restart

# checks container status
./container.py status

# checks container command output 
./container.py logs
```

And for individual container you can do

```bash
# builds container image using Dockerfile and brings up container with settings chosen in docker-compose.yaml 
./container.py up containerNameHere

# attaches bash session to container 
./container.py attach containerNameHere

# restarts container
./container.py restart containerNameHere

# brings down container
./container.py down containerNameHere

# checks container status
./container.py status containerNameHere

# checks container command output 
./container.py logs containerNameHere
```

## Setup

If using this template just be sure to match this folder structure for containers and specify the `name` and `folder` under `container_X` in the `container_config.yaml`

**Leave `container_X` key format in the `container_config.yaml` as well as the `[container_X]` comments`docker-compose.yaml` as is!!**
