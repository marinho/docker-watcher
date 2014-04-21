#!/usr/bin/env python

__version__ = "0.1"
__author__ = "Marinho Brandao"

import sys
import argparse
import ConfigParser
from docker_watcher.services import Container, _commands


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, default="/etc/docker-watcher/docker-watcher.conf")
    args, remaining_args = parser.parse_known_args()
    return args, remaining_args


def read_config_file(filename):
    config = ConfigParser.RawConfigParser()
    config.read(filename)
    return config


def load_containers(config):
    for section in config.sections():
        tmp, name = section.split(":")
        container = Container.from_dict(name, dict(config.items(section)))


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
