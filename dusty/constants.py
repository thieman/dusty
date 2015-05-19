import os

SOCKET_TERMINATOR = '\0\0'

LOCALHOST = "127.0.0.1"

ROOT_LOG_DIR = '/var/log/dusty'
LOG_SUBDIRS = ['nginx']

SOCKET_PATH = '/var/run/dusty/dusty.sock'
CONFIG_PATH = '/etc/dusty/config.yml'
REPOS_DIR = '/etc/dusty/repos'
COMPOSE_DIR = '/etc/dusty/compose'
FIRST_RUN_FILE_PATH = '/var/run/dusty/docker_first_time_started'

GIT_USER = 'git'

HOSTS_PATH = '/etc/hosts'

VIRTUALBOX_RULE_PREFIX = 'dusty'

NGINX_PID_PATH = '/usr/local/var/run/nginx.pid'
NGINX_CONFIG_INCLUDES_DIR = '/usr/local/etc/nginx/servers'

SYSTEM_DEPENDENCY_VERSIONS = {
    'nginx': '1.8.0',
    'virtualbox': '4.3.26',
    'boot2docker': '1.6.0',
    'docker': '1.6.0'
}

CONFIG_KEY_WHITELIST = [
    'bundles',
    'repo_overrides',
    'specs_path',
    'docker_user'
]
