import os

import docker

from .. import constants
from ..log import log_to_client
from ..path import dir_modified_time, set_mac_user_ownership
from ..systems.docker.cleanup import remove_exited_dusty_containers, remove_images
from ..systems.virtualbox import get_docker_vm_disk_info, ensure_docker_vm_is_started, initialize_docker_vm
from ..systems.rsync import sync_local_path_to_vm, sync_local_path_from_vm
from ..payload import daemon_command

@daemon_command
def cleanup_inactive_containers():
    ensure_docker_vm_is_started()
    log_to_client("Cleaning up exited containers:")
    containers = remove_exited_dusty_containers()
    log_to_client("Done cleaning {} containers".format(len(containers)))

@daemon_command
def cleanup_images():
    ensure_docker_vm_is_started()
    log_to_client("Cleaning up docker images without containers:")
    images = remove_images()
    log_to_client("Done removing {} images".format(len(images)))

@daemon_command
def inspect_vm_disk():
    ensure_docker_vm_is_started()
    log_to_client("Dusty VM Disk Usage:")
    log_to_client(get_docker_vm_disk_info())

def _full_backup_dir(path):
    if path.endswith(constants.LOCAL_BACKUP_DIR):
        return path
    return os.path.join(path, constants.LOCAL_BACKUP_DIR)

def _ensure_backup_dir_exists(destination_path):
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

@daemon_command
def backup(path):
    destination_path = _full_backup_dir(path)
    _ensure_backup_dir_exists(destination_path)
    initialize_docker_vm()
    log_to_client("Syncing data from your VM to {}...".format(destination_path))
    sync_local_path_from_vm(destination_path, constants.VM_PERSIST_DIR)
    set_mac_user_ownership(destination_path)

@daemon_command
def restore(path):
    source_path = _full_backup_dir(path)
    if not os.path.exists(source_path):
        log_to_client("Can't find backup data to restore at {}".format(source_path))
        return
    initialize_docker_vm()
    log_to_client("Restoring your backup last modified at {}".format(dir_modified_time(source_path)))
    sync_local_path_to_vm(source_path, constants.VM_PERSIST_DIR)
