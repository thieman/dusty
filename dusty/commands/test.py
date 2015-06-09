from ..compiler.spec_assembler import get_expanded_libs_specs
from ..compiler.compose import get_app_volume_mounts, get_lib_volume_mounts, get_testing_compose_dict
from ..systems.docker.testing_image import ensure_image_exists
from ..systems.docker import get_docker_client
from ..systems.docker.compose import write_composefile
from ..systems.rsync import sync_repos_by_app_name, sync_repos_by_lib_name
from ..log import log_to_client

def run_app_or_lib_tests(app_or_lib_name, force_recreate=False):
    docker_client = get_docker_client()
    expanded_specs = get_expanded_libs_specs()
    if app_or_lib_name in expanded_specs['apps']:
        volumes = get_app_volume_mounts(app_or_lib_name, expanded_specs)
        spec = expanded_specs['apps'][app_or_lib_name]
        sync_repos_by_app_name(expanded_specs, [app_or_lib_name])
    elif app_or_lib_name in expanded_specs['libs']:
        volumes = get_lib_volume_mounts(app_or_lib_name, expanded_specs)
        spec = expanded_specs['libs'][app_or_lib_name]
        sync_repos_by_lib_name(expanded_specs, [app_or_lib_name])
    else:
        raise RuntimeError('Argument must be defined app or lib name')

    image_name = "{}_dusty_testing/image".format(app_or_lib_name)
    ensure_image_exists(docker_client, spec['test'], image_name, volumes=volumes, force_recreate=force_recreate)
    _run_tests_with_image(app_or_lib_name)

def _run_tests_with_image(expanded_specs, app_or_lib_name, app_or_lib_spec, app_or_lib_volumes, image_name):
    temporary_compose_config_files = []
    previous_container_name = None

    for service_name in app_or_lib_spec['test']['services']:
        service_spec = expanded_specs['services'][service_name]
        kwargs = {}
        if previous_container_name is not None:
            kwargs['net_container_identifier'] = previous_container_name
        service_compse_config = get_testing_compose_dict(service_name, service_spec, **kwargs)
        #make a compose_file
        temporary_compose_config_files.append(compose_file)
        write_composefile(service_compse_config, compose_file)
