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

    # set service name in the docker-compose.yaml using container config name
    @staticmethod
    def init_composefile_service_name(composefile):
        # get parent directory
        parentdir = Path.cwd().parent.name
        
        envlist = []

        # read lines
        with open(composefile, 'r') as f:
            lines = f.readlines()
        # replace service name
        replaceNextLines = False
        triggerline = '[container_'
        service_key, service_name = None, None
        for idx, line in enumerate(lines):
            if replaceNextLines:
                lines[idx] = f'  {service_name}_service:\n'
                replaceNextLines = False
            elif triggerline in line:
                replaceNextLines = True
                service_key =  line[line.find('[')+1:line.find(']')]
                service_name = cfg[service_key]['name']
                service_folder = cfg[service_key]['folder']
                # udpate env list with service params
                envlist.append(f'{service_key}={service_name}')
                envlist.append(f'{service_key}_folder={service_folder}')

        # write lines
        with open(composefile, 'w') as f:
            f.writelines(lines)

        return envlist

    def __init__(self) -> None:
        pass

    @classmethod
    def getProjectStatus(cls, envlist, status_cmd_str):
        # prep env file before checking
        cls.prep_env_file(envlist)
        ret = cls.execute_cmd_getoutput(status_cmd_str)
        lines = ret.split('\n')
        container_status_lines = lines[2:]

        # print(f'status lines: {container_status_lines}')

        # code.interact(local=locals())

        statuses = []

        if len(container_status_lines) == 0:
            return 'Down', None
        for line in container_status_lines:
            if line:
                spl = line.split()
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
                f'overall status is mixed. you may want to check on this!!!!'
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
        parentdir = Path.cwd().parent.name
        envlist = cls.getSharedDockerComposeEnv()
        composefile = 'docker-compose.yaml'
        service_env_list = cls.init_composefile_service_name(composefile)
        envlist.extend(service_env_list)
        projectname = f"{parentdir}_{cfg['project_name']}"
        cmdlist = cls.parseaction(composefile, projectname, args.container, envlist)
        return cmdlist, envlist

    
    @classmethod
    def parseaction(cls, composefile, projectname, container_name, envlist):
        cmdlist = []

        parentdir = Path.cwd().parent.name
        service_name = f'{container_name}_service'
        instance_name = f'{container_name}_instance_{parentdir}'

        # create command strings for all or container here
        cmd_start = f'docker-compose -f {composefile} -p {projectname}'

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
        if container_name == 'all':           
            status, _stats = cls.getProjectStatus(envlist, cmd_status_all)
        else:
            status, _stats = cls.getProjectStatus(envlist, cmd_status_container)

        # actually parse action and append appropriate commands to execute
        if args.action == 'up':
            if container_name == 'all':
                if status == 'Up':
                    print(f'project {projectname} is already up!!')
                    exit(1)
                else:
                    cmdlist.append(cmd_up_all)
            else:
                if status == 'Up':
                    print(f'container {container_name} is already up!!')
                    exit(1)
                else:
                    cmdlist.append(cmd_up_container)

        elif args.action == 'down':
            if container_name == 'all': 
                cmdlist.append(cmd_down_all)
            else:
                cmdlist.append(cmd_down_container)

        elif args.action == 'restart':
            if container_name == 'all':
                cmdlist.append(cmd_restart_all)
            else:
                cmdlist.append(cmd_restart_container)

        elif args.action == 'attach':
            if container_name == 'all':
                print('must specify a container to attach to')
                print('options: {get_options_here_later}')
                exit(1)
            else:
                print(f'attaching to container instance {instance_name}...')
                cmdlist.append(cmd_attach_container)

        elif args.action == 'logs':
            if container_name == 'all':
                cmdlist.append(cmd_log_all)
            else:
                cmdlist.append(cmd_log_container)

        elif args.action == 'status':
            if container_name == 'all':
                cmdlist.append(cmd_status_all)
            else:
                cmdlist.append(cmd_status_container)
                
        else:
            raise Exception(f'unrecognized action {args.action}!')

        return cmdlist
    
    @classmethod
    def execute_cmd(cls, cmdstr):
        subprocess.Popen(cmdstr, shell=True).wait()

    @classmethod
    def execute_cmd_getoutput(cls, cmdstr):
        # old cmd: subprocess.check_output(cmdstr.split()).decode('utf-8')
        # lines = subprocess.check_output(cmdstr.split()).decode('utf-8')
        # proc = subprocess.Popen(cmdstr, shell=True, stdout=subprocess.PIPE)
        # lines = io.TextIOWrapper(proc.stdout, encoding="utf-8").readlines()
        # return lines
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

    @classmethod
    def verify_container(cls, container_name):
        container_list = ['all']
        for key in cfg.keys():
            if key != 'project_name':
                container_list.append(cfg[key]['name'])
        valid = (container_name in container_list)
        if not valid:
            err_msg = f'invalid container name {container_name}\n'
            err_msg += f'must be from list'
            raise Exception()

    class ValidateContainerArg(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            container_list = ['all']
            for key in cfg.keys():
                if key != 'project_name':
                    container_list.append(cfg[key]['name'])
            
            if values not in container_list:
                raise argparse.ArgumentError(
                    self, f'\'{values}\' not in container list: {container_list}')
            setattr(namespace, self.dest, values)

if __name__ == '__main__':

    # Multi-container arg parsing (single compose file)
    # Note: this is not same as multi-project where multiple compose files are used. 
    #       that'll be a separate branch later once I get the time

    parser = argparse.ArgumentParser()

    # actions to do on each container
    action_parser = parser.add_subparsers(title='action', dest='action', help='action to do on container', required=True)
    actions = []
    actions.append(action_parser.add_parser('up'))
    actions.append(action_parser.add_parser('down'))
    actions.append(action_parser.add_parser('restart'))
    actions.append(action_parser.add_parser('logs'))
    actions.append(action_parser.add_parser('status'))
    actions.append(action_parser.add_parser('attach'))

    # append additional params to actions here
    for action in actions:
        action.add_argument('container',
            help='container to attach to',
            nargs='?',
            default='all',
            action=CommandManager.ValidateContainerArg)

    # parse args
    args = parser.parse_args()

    #### take action on args below ####
    cmdlist, envlist = CommandManager.parsecommand(args)
    CommandManager.execute_cmdlist(cmdlist, envlist)
