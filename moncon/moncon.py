import os
import sys
import json
import argparse
import configparser
import requests

MONYOG_BOOL_ACTIONS = (
    'alerts',
    'datacollection',
    'sniffer',
    'longrunningqueries',
    'lockedqueries')

MONYOG_LONG_ACTIONS = (
    'longrunningqueryaction')


def cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default=5555)
    parser.add_argument('--user')
    parser.add_argument('--password')

    parser.add_argument('--server')
    parser.add_argument('--tags')

    subparsers = parser.add_subparsers()

    # Enable/Disable actions
    bool_parser = subparsers.add_parser(
            'enable_disable')
    bool_parser.add_argument(
        'action', choices=MONYOG_BOOL_ACTIONS)
    bool_parser.add_argument(
        'value', choices=('enable', 'disable'))

    # Long Running Query Actions
    long_parser = subparsers.add_parser(
            'long_running')
    long_parser.add_argument(
            'action', choices=MONYOG_LONG_ACTIONS)
    long_parser.add_argument(
            'value', choices=('notify', 'kill', 'notifyandkill'))

    args = parser.parse_args()

    cfg = {
        'host': str(args.url),
        'port': str(args.port),
        '_action': args.action,
        '_value': args.value}

    if args.server and args.tag:
        print("Choose only one of --server or --tag")
        sys.exit(2)
    else:
        if args.server:
            cfg['target'] = '_server={}'.format(args.server)
        elif args.tags:
            cfg['target'] = '_tags={}'.format(args.tags)

        if args.password:
            cfg['_password'] = str(args.password)
        if args.user:
            cfg['_user'] = str(args.user)

        print(**cfg)
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
    cfg = configparser.ConfigParser()
    cfg.read(cnf_path)
    if section in cfg.sections:
        return cfg[section]
    else:
        return False


def read_configs(section='monyog'):
    my_cnf_file = my_cnf()
    system_cnf_files = system_cnf()
    if my_cnf_file:
        return read_config(my_cnf_file, section)
    elif system_cnf_files:
        #  Read files in paths in a linear order.
        #  Break as soon as we find valid monyog details.
        for i in system_cnf_files:
            if read_config(i, section):
                return i
    else:
        sys_paths = ', '.join(system_cnf_files)
        sys.exit("No {s} found in {m} or any of: {c}".format(
            s=section,
            m=my_cnf_file,
            c=sys_paths))


def monyog_cfg(cfg: dict = cli_args()):
    file_cfg = read_configs()
    cli_cfg = cfg.copy()
    cfg = dict()

    if file_cfg():
        cfg.update(file_cfg)

    if cli_cfg:
        cfg.update(cli_cfg)

    cfg['_object'] = 'MONyogAPI'

    url_template = (
        "http://{host}:{port}/"
        "?_object={_object}"
        "&_action={_action}"
        "&_value={_value}"
        "{target}")

    fmt_url = url_template.format(**cfg)
    cfg['url'] = fmt_url
    print(cfg)
    return cfg


def monyog_cmd(cfg: dict = monyog_cfg()):
    r = requests.get(cfg['url'])
    return r.json()


def check_status(status):
    s = json.load(status)
    print(s)


def main():
    cli_args()
    # monyog_cfg()

