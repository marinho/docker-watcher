#!/usr/bin/env python

__version__ = "0.1"
__author__ = "Marinho Brandao"

import sys
import argparse
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from docker_watcher.services import Container, _commands


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, default="/etc/docker-watcher/docker-watcher.yml")
    args, remaining_args = parser.parse_known_args()
    return args, remaining_args


def read_config_file(filename):
    fp = file(filename)
    config = yaml.load(fp, Loader=Loader)
    fp.close()

    return config


def load_containers(config):
    for name, item in config.items():
        container = Container.from_dict(name, item)


def run():
    args, other_args = get_args()
    if not other_args:
        sys.exit("A command is required.")
    elif other_args[0] not in _commands:
        sys.exit("Command '%s' is not supported." % other_args[0])
    cmd = _commands[other_args[0]]

    config = read_config_file(args.config)
    containers = load_containers(config)

    cmd(*other_args[1:])
