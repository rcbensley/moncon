import os
import sys
import urllib
import argparse
import configparser

MONYOG_KEYS = ('url',
               'port',
               '_user',
               '_password')


def cli_args():
    return


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


def read_config(cnf_path, section='monyog', keys=MONYOG_KEYS):
    cfg = configparser.ConfigParser()
    cfg.read(cnf_path)
    if section in cfg.sections:
        missing_keys = False
        for k in keys:
            if k not in cfg[section]:
                missing_keys = True
        if missing_keys is True:
            return False
        else:
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
        sys.exit("No {s} found in {m} or any of: {c}".format(s=section,
                                                             m=my_cnf_file,
                                                             c=sys_paths))


def monyong_cmd(cfg: dict, operation: str):
    def fmt_cmd(d, k):
        s = "{k}={v}".format(**d)
        return s

    def join_cmd(d, keys):
        cmds = []
        for i in keys:
            cmds.append(fmt_cmd(d, i))
        joined_cmd = '&'.join(cmds)
        return joined_cmd

    monyog_cfg = cfg.copy()
    monyog_cfg['_object'] = 'MONyogAPI'
    monyog_cfg['object'] = fmt_cmd(monyog_cfg, '_object')

    url_template = "http://{url}:{port}/?{object}{cmd}"
    fmt_url = url_template.format(**monyog_cfg)
    return fmt_url
