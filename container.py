#!/usr/bin/env python3

import code

import argparse
from pathlib import Path
import io
import subprocess
import platform
import yaml

# load container config
with open('container_config.yaml', 'r') as f:
    cfg = yaml.safe_load(f)

class CommandManager:

    ### choose your docker compose command here based on docker version
    # docker_compose_cmd = 'docker-compose'
    docker_compose_cmd = 'docker compose'

    # name of container stuff
    basename = cfg['name']

    # choices of actions you can take
    action_choices = ('up', 'down', 'restart', 'attach', 'logs', 'status')

    # set service name in the docker-compose.yaml using container config name
    @classmethod
    def init_composefile_service_name(cls, composefile):
        # get parent directory
        parentdir = Path.cwd().parent.name
        
        envlist = []

        # read lines
        with open(composefile, 'r') as f:
            lines = f.readlines()
        # replace service name
        replaceNextLine = False
        triggerline = '[service name below]'
        for idx, line in enumerate(lines):
            if replaceNextLine:
                lines[idx] = f'  {cls.basename}_service:\n'
                break
            elif triggerline in line:
                replaceNextLine = True
        # write lines
        with open(composefile, 'w') as f:
            f.writelines(lines)

    class ValidateCamGroupNum(argparse.Action):
        cameragroup_range = range(0, 100)

        def __call__(self, parser, namespace, values, option_string=None):
            if values not in self.cameragroup_range:
                raise argparse.ArgumentError(
                    self, f'not in range {self.cameragroup_range}')
            setattr(namespace, self.dest, values)

    def __init__(self) -> None:
        pass

    @staticmethod
    def getParentDirectory():
      # ensure lower case for project naming
      return Path.cwd().parent.name.lower()

    @classmethod
    def getProjectStatus(cls, envlist, status_cmd_str):
        print(f'{status_cmd_str}')
        # prep env file before checking
        cls.prep_env_file(envlist)
        ret = cls.execute_cmd_getoutput(status_cmd_str)
        lines = ret.split('\n')
        if 'no such service' in lines[0]:
            return 'Down', None

        container_status_lines = lines[1:]
        # print(container_status_lines)

        statuses = []

        if len(container_status_lines) == 0:
            return 'Down', None
        for line in container_status_lines:
            if line:
                spl = line.split()
                parsed_container_name = spl[0]
                cleaned = [word.strip() for word in spl]
                if 'Up' in cleaned or 'running' in cleaned:
                    status = 'Up'
                else:
                    status = 'Down'
                statuses.append((parsed_container_name, status))
        status_set = set([s[1] for s in statuses])
        if len(status_set) == 0:
            return 'Down', None
        elif len(status_set) == 1:
            overall_status = list(status_set)[0]
        else:
            overall_status = 'mixed'
            print(
                f'overall status is mixed. you may want to check on this!!!!'
            )
            print(statuses)
        return overall_status, statuses

    @staticmethod
    def getSharedDockerComposeEnv():
        starting_env = []
        arch = platform.machine()
        parentdir = CommandManager.getParentDirectory()
        starting_env.append(f'ARCH={arch}')
        starting_env.append(f'PARENTDIR={parentdir}')
        starting_env.append(f'FROM_IMG_GPU=pwolfe854/gst_ds_env:{arch}_gpu')
        starting_env.append(f'FROM_IMG_NOGPU=pwolfe854/gst_ds_env:{arch}_nogpu')
        starting_env.append(f'MAP_DISPLAY=/tmp/.X11-unix/:/tmp/.X11-unix')
        starting_env.append(f'MAP_SSH=~/.ssh:/root/.ssh:ro')
        starting_env.append(f'MAP_TIMEZONE=/etc/localtime:/etc/localtime:ro')
        return starting_env

    @classmethod
    def parsecommand(cls, args):
        # TODO make a multiple container example here 
        parentdir = cls.getParentDirectory()
        envlist = cls.getSharedDockerComposeEnv()
        basename = cls.basename.lower()
        envlist.append(f'BASENAME={basename}')
        composefile = 'docker-compose.yaml'
        cls.init_composefile_service_name(composefile)
        projectname = f'{parentdir}_{basename}'
        container_name = f'{basename}'
        cmdlist = cls.parseaction(composefile, projectname, container_name, envlist)
        
        return cmdlist, envlist

    
    @classmethod
    def parseaction(cls, composefile, projectname, container_name, envlist):
        cmdlist = []

        parentdir = cls.getParentDirectory()
        service_name = f'{container_name}_service'
        instance_name = f'{container_name}_instance_{parentdir}'

        # create command strings for all or container here
        cmd_start = f'docker compose -f {composefile} -p {projectname}'

        cmd_up_all = f'{cmd_start} up --detach --build'
        cmd_up_container = f'{cmd_up_all} {service_name}'

        cmd_down_all = f'{cmd_start} down -t 0'
        cmd_down_container = f'{cmd_start} stop {service_name} -t 0 && {cmd_start} rm -f {service_name}'

        cmd_restart_all = f'{cmd_start} restart -t 0'
        cmd_restart_container = f'{cmd_restart_all} {service_name}'

        cmd_attach_container = f'docker exec -it {instance_name} /bin/bash'

        cmd_log_all = f'{cmd_start} logs -f'
        cmd_log_container = f'{cmd_log_all} {service_name}'

        cmd_status_all = f'{cmd_start} ps'
        cmd_status_container = f'{cmd_status_all} {service_name}'

        # check status first
        status, _stats = cls.getProjectStatus(envlist, cmd_status_container)
        print(f'{status=}')

        if args.action == 'up':
            if status == 'Up':
                print(f'project {projectname} is already up!!')
                exit(1)
            else:
                cmdlist.append(cmd_up_all)
        elif args.action == 'down':
            cmdlist.append(cmd_down_all)
        elif args.action == 'restart':
            cmdlist.append(cmd_restart_all)
        elif args.action == 'attach':
            if status == 'Down':
                print(f'seems project {projectname} is not up')
                exit(1)
            print(f'attaching to container {container_name}...')
            cmdlist.append(cmd_attach_container)
        elif args.action == 'logs':
            if status == 'Down':
                print(f'seems project {projectname} is not up')
                exit(1)
            cmdlist.append(cmd_log_all)
        elif args.action == 'status':
            cmdlist.append(cmd_status_all)
        else:
            raise Exception(f'unrecognized action {args.action}!')
        return cmdlist
    
    @classmethod
    def execute_cmd(cls, cmdstr):
        subprocess.Popen(cmdstr, shell=True).wait()

    @classmethod
    def execute_cmd_getoutput(cls, cmdstr):
        # return subprocess.check_output(cmdstr.split()).decode('utf-8')
        try:
            ret = subprocess.check_output(cmdstr, shell=True, stderr=subprocess.STDOUT)
            return ret.decode('utf-8')
        except subprocess.CalledProcessError as e:
            return e.output.decode('utf-8')

    @classmethod 
    def prep_env_file(cls, envlist):
        # prep .env file
        with open('.env', 'w') as f:
            for line in envlist:
                f.write(f'{line}\n')

    @classmethod
    def execute_cmdlist(cls, cmdlist, envlist):
        # check for empty command list
        if len(cmdlist) == 0:
            print(f'no commands present in command list. returning...')
            return
        # prep .env file
        cls.prep_env_file(envlist)
        # execute command list
        for cmd in cmdlist:
            print(f'executing {cmd}')
            cls.execute_cmd(cmd)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',
                        help='action to do on local track handler container',
                        choices=CommandManager.action_choices)

    args = parser.parse_args()
    cmdlist, envlist = CommandManager.parsecommand(args)
    CommandManager.execute_cmdlist(cmdlist, envlist)
