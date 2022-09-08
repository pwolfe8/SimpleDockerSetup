#!/usr/bin/python3

import code

import argparse
from pathlib import Path
import io
import subprocess
import platform
import yaml

# load container config
with open('ContainerConfig.yaml', 'r') as f:
    cfg = yaml.safe_load(f)

class CommandManager:
    
    # name of container stuff
    basename = cfg['name']

    # choices of actions you can take
    action_choices = ('up', 'down', 'restart', 'attach', 'logs', 'status')

    # set service name in the docker-compose.yaml using container config name
    @staticmethod
    def init_composefile_service_name(composefile):
        # get basename from container config yaml
        basename = cfg['name']
        # read lines
        with open(composefile, 'r') as f:
            lines = f.readlines()
        # replace service name
        replaceNextLine = False
        triggerline = '[service name below]'
        for idx, line in enumerate(lines):
            if replaceNextLine:
                lines[idx] = f'  {basename}_service:\n'
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

    @classmethod
    def getProjectStatus(cls, projectname, composefile, envlist):
        # prep env file before checking
        cls.prep_env_file(envlist)
        # check
        statuses = []
        cmd = f'COMPOSE_FILE={composefile} docker-compose -p {projectname} ps'
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        lines = io.TextIOWrapper(proc.stdout, encoding="utf-8").readlines()
        container_status_lines = lines[2:]
        # print(f'status lines: {container_status_lines}')
        if len(container_status_lines) == 0:
            return 'Down', None
        for line in container_status_lines:
            spl = line.split()
            # print(f'split: {spl}')
            parsed_container_name = spl[0]
            if 'Up' in [word.strip() for word in spl]:
                status = 'Up'
            else:
                status = 'Down'
            statuses.append((parsed_container_name, status))
        status_set = set([s[1] for s in statuses])
        if len(status_set) == 1:
            overall_status = list(status_set)[0]
        else:
            overall_status = 'mixed'
            print(
                f'project {projectname} overall status is mixed. you may want to check on this!!!!'
            )
            print(statuses)
        return overall_status, statuses

    @staticmethod
    def getSharedDockerComposeEnv():
        starting_env = []
        arch = platform.machine()
        parentdir = Path.cwd().parent.name
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
        parentdir = Path.cwd().parent.name
        envlist = cls.getSharedDockerComposeEnv()
        basename = cls.basename
        envlist.append(f'BASENAME={basename}')
        composefile = 'docker-compose.yaml'
        cls.init_composefile_service_name(composefile)
        projectname = f'{parentdir}_{basename}'
        containername = f'{basename}_instance_{parentdir}'
        cmdlist = cls.parseaction(composefile, projectname, containername, envlist)
        
        return cmdlist, envlist

    
    @classmethod
    def parseaction(cls, composefile, projectname, containername, envlist):
        cmdlist = []

        # check status first
        status, _stats = cls.getProjectStatus(projectname, composefile, envlist)

        # check action and choose appropriate commands
        cmdstart = f'docker-compose -f {composefile} -p {projectname}'
        upcmd = f'{cmdstart} up --detach --build'
        downcmd = f'{cmdstart} down -t 0'
        attachcmd = f'docker exec -it {containername} /bin/bash'
        logcmd = f'COMPOSE_FILE={composefile} docker-compose -p {projectname} logs -f'
        statuscmd = f'COMPOSE_FILE={composefile} docker-compose -p {projectname} ps'

        if args.action == 'up':
            if status == 'Up':
                print(f'project {projectname} is already up!!')
                exit(1)
            else:
                cmdlist.append(upcmd)
        elif args.action == 'down':
            if status == 'Down':
                print(f'seems project {projectname} is already down')
                exit(1)
            else:
                cmdlist.append(downcmd)
        elif args.action == 'restart':
            cmdlist.append(downcmd)
            cmdlist.append(upcmd)
        elif args.action == 'attach':
            if status == 'Down':
                print(f'seems project {projectname} is not up')
                exit(1)
            print(f'attaching to container {containername}...')
            cmdlist.append(attachcmd)
        elif args.action == 'logs':
            if status == 'Down':
                print(f'seems project {projectname} is not up')
                exit(1)
            cmdlist.append(logcmd)
        elif args.action == 'status':
            cmdlist.append(statuscmd)
        else:
            raise Exception(f'unrecognized action {args.action}!')
        return cmdlist
    
    @classmethod
    def execute_cmd(cls, cmdstr):
        subprocess.Popen(cmdstr, shell=True).wait()

    @classmethod
    def execute_cmd_getoutput(cls, cmdstr):
        return subprocess.check_output(cmdstr.split()).decode('utf-8')

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
