import os
import logging
import subprocess
from copy import copy
import re

import yaml

from ... import constants
from ...config import get_config_value, assert_config_key
from ...demote import check_output_demoted, check_call_demoted

def _get_docker_env():
    output = check_output_demoted(['boot2docker', 'shellinit'])
    env = {}
    for line in output.splitlines():
        k, v = line.strip().split()[1].split('=')
        env[k] = v
    return env

def _composefile_path():
    return os.path.join(constants.COMPOSE_DIR, 'docker-compose.yml')

def _write_composefile(compose_config):
    logging.info('Writing new Composefile')
    if not os.path.exists(constants.COMPOSE_DIR):
        os.makedirs(constants.COMPOSE_DIR)
    with open(_composefile_path(), 'w') as f:
        f.write(yaml.dump(compose_config, default_flow_style=False))

def _compose_up():
    logging.info('Running docker-compose up')
    check_call_demoted(['docker-compose', '-f', _composefile_path(), '-p', 'dusty', 'up', '-d', '--allow-insecure-ssl'],
                       env=_get_docker_env())

def update_running_containers_from_spec(compose_config):
    """Takes in a Compose spec from the Dusty Compose compiler,
    writes it to the Compose spec folder so Compose can pick it
    up, then does everything needed to make sure boot2docker is
    up and running containers with the updated config."""
    assert_config_key('mac_username')
    _write_composefile(compose_config)
    _compose_up()