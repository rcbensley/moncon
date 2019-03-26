import os
import sys
import json
import argparse
import configparser
from pprint import pprint
import requests

ACTIONS_BOOL = (
    'alerts',
    'datacollection',
    'sniffer',
    'longrunningqueries',
    'lockedqueries')

VALUES_BOOL = (
    'enable',
    'disable')

ACTIONS_LONG = (
    'longrunningqueryaction',)

VALUES_LONG = (
    'notify',
    'kill',
    'notifyandkill')

ACTIONS_ALL = list(ACTIONS_BOOL) + list(ACTIONS_LONG)


def bomb(msg, x=2):
    print(msg)
    sys.exit(x)


def cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default=5555)
    parser.add_argument('--user')
    parser.add_argument('--password')
    parser.add_argument('--server')
    parser.add_argument('--tags')
    parser.add_argument('--action', required=True)
    parser.add_argument('--value', required=True)
    parser.add_argument('--dry-run', action='store_true', default=False)
    args = parser.parse_args()

    cfg = {
        'host': str(args.host),
        'port': str(args.port),
        'dry_run': args.dry_run}

    if args.action not in ACTIONS_ALL:
        bomb("Action must be one of {} {}".format(
            ', '.join(ACTIONS_ALL)))
    elif args.action in ACTIONS_BOOL and args.value not in VALUES_BOOL:
        bomb("{} is not a valid value for {}".format(
            args.value, args.value))
    elif args.action in ACTIONS_LONG and args.value not in VALUES_LONG:
        bomb("{} is not a valid value for {}".format(
            args.value, args.value))
    else:
        cfg['action'] = args.action
        cfg['value'] = args.value

    if args.server and args.tags:
        bomb("Choose only one of --server or --tags")

    if args.server:
        cfg['target'] = '_server={}'.format(args.server)
    elif args.tags:
        cfg['target'] = '_tags={}'.format(args.tags)
    else:
        bomb("Need at least one of --server or --tags")

    if args.password:
        cfg['password'] = str(args.password)
    if args.user:
        cfg['user'] = str(args.user)

    return cfg


def my_cnf():
    cnf_path = os.path.expanduser('~/.my.cnf')
    if os.path.isfile(cnf_path):
        return cnf_path
    else:
        return False


def system_cnf():
    paths = ('/etc/my.cnf',
             '/etc/my.cnf.d/mariadb.cnf')
    found_files = []
    for i in paths:
        if os.path.isfile(i) and os.access(i, os.W_OK):
            found_files.append(i)
            break
    if found_files:
        return found_files
    else:
        return False


def read_config(cnf_path, section='monyog'):
    cfg = configparser.ConfigParser(allow_no_value=True)
    cfg.read(cnf_path)
    if section in cfg.sections():
        return dict(cfg[section])
    else:
        return False


def read_configs(section='monyog'):
    my_cnf_file = my_cnf()
    system_cnf_files = system_cnf()
    if my_cnf_file:
        cfg = read_config(my_cnf_file, section)
    elif system_cnf_files:
        #  Read files in paths in a linear order.
        #  Break as soon as we find valid monyog details.
        for i in system_cnf_files:
            if read_config(i, section):
                cfg = i
                break
    else:
        sys_paths = ', '.join(system_cnf_files)
        sys.exit("No {s} found in {m} or any of: {c}".format(
            s=section,
            m=my_cnf_file,
            c=sys_paths))

    return cfg


def monyog_cfg(cfg: dict = cli_args()):
    file_cfg = read_configs()
    cli_cfg = cfg.copy()
    cfg = dict()

    if file_cfg:
        cfg.update(file_cfg)

    if cli_cfg:
        cfg.update(cli_cfg)

    cfg['object'] = 'MONyogAPI'

    url_template = (
        "http://{host}:{port}/"
        "?_object={object}"
        "&_action={action}"
        "&_value={value}"
        "&_user={user}"
        "&_password={password}"
        "&{target}")

    fmt_url = url_template.format(**cfg)
    cfg['url'] = fmt_url
    return cfg


def monyog_cmd(cfg: dict = monyog_cfg()):
    if cfg['dry_run']:
        pprint(cfg)
        return
    else:
        r = requests.get(cfg['url'])
        return r.json()


def check_status(status):
    s = json.load(status)
    return s


def main():
    monyog_cmd()
