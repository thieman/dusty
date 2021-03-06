import logging

from ..config import get_config_value
from .. import constants
from ..memoize import memoized
from ..source import Repo
from ..schemas.app_schema import app_schema
from ..schemas.bundle_schema import bundle_schema
from ..schemas.lib_schema import lib_schema
from ..schemas.base_schema_class import DustySchema, DustySpecs

def _get_dependent(dependent_type, name, specs, root_spec_type):
    """
    Returns everything of type <dependent_type> that <name>, of type <root_spec_type> depends on
    Names only are returned in a set
    """
    spec = specs[root_spec_type].get(name)
    if spec is None:
        raise RuntimeError("{} {} was referenced but not found".format(root_spec_type, name))
    dependents = spec['depends'][dependent_type]
    all_dependents = set(dependents)
    for dep in dependents:
        all_dependents |= _get_dependent(dependent_type, dep, specs, dependent_type)
    return all_dependents

def _get_active_bundles(specs):
    return set(get_config_value(constants.CONFIG_BUNDLES_KEY))

def _get_referenced_apps(specs):
    """
    Returns a set of all apps that are required to run any bundle in specs[constants.CONFIG_BUNDLES_KEY]
    """
    activated_bundles = specs[constants.CONFIG_BUNDLES_KEY].keys()
    all_active_apps = set()
    for active_bundle in activated_bundles:
        bundle_spec = specs[constants.CONFIG_BUNDLES_KEY].get(active_bundle)
        for app_name in bundle_spec['apps']:
            all_active_apps.add(app_name)
            all_active_apps |= _get_dependent('apps', app_name, specs, 'apps')
    return all_active_apps

def _expand_libs_in_apps(specs):
    """
    Expands specs.apps.depends.libs to include any indirectly required libs
    """
    for app_name, app_spec in specs['apps'].iteritems():
        if 'depends' in app_spec and 'libs' in app_spec['depends']:
            app_spec['depends']['libs'] = _get_dependent('libs', app_name, specs, 'apps')

def _expand_libs_in_libs(specs):
    """
    Expands specs.libs.depends.libs to include any indirectly required libs
    """
    for lib_name, lib_spec in specs['libs'].iteritems():
        if 'depends' in lib_spec and 'libs' in lib_spec['depends']:
            lib_spec['depends']['libs'] = _get_dependent('libs', lib_name, specs, 'libs')

def _get_referenced_libs(specs):
    """
    Returns all libs that are referenced in specs.apps.depends.libs
    """
    active_libs = set()
    for app_spec in specs['apps'].values():
        for lib in app_spec['depends']['libs']:
            active_libs.add(lib)
    return active_libs

def _get_referenced_services(specs):
    """
    Returns all services that are referenced in specs.apps.depends.services,
    or in specs.bundles.services
    """
    active_services = set()
    for app_spec in specs['apps'].values():
        for service in app_spec['depends']['services']:
            active_services.add(service)
    for bundle_spec in specs['bundles'].values():
        for service in bundle_spec['services']:
            active_services.add(service)
    return active_services

def _filter_active(spec_type, specs):
    get_referenced = {
        constants.CONFIG_BUNDLES_KEY: _get_active_bundles,
        'apps': _get_referenced_apps,
        'libs': _get_referenced_libs,
        'services': _get_referenced_services
    }
    active = get_referenced[spec_type](specs)
    all_specs = specs[spec_type].keys()
    for item_name in all_specs:
        if item_name not in active:
            del specs[spec_type][item_name]
    logging.debug("Spec Assembler: filtered active {} to {}".format(spec_type, set(specs[spec_type].keys())))

def _add_active_assets(specs):
    """
    This function adds an assets key to the specs, which is filled in with a dictionary
    of all assets defined by apps and libs in the specs
    """
    specs['assets'] = {}
    for spec in specs.get_apps_and_libs():
        for asset in spec['assets']:
            if not specs['assets'].get(asset['name']):
                specs['assets'][asset['name']] = {}
                specs['assets'][asset['name']]['required_by'] = set()
                specs['assets'][asset['name']]['used_by'] = set()
            specs['assets'][asset['name']]['used_by'].add(spec.name)
            if asset['required']:
                specs['assets'][asset['name']]['required_by'].add(spec.name)

def _get_expanded_active_specs(specs):
    """
    This function removes any unnecessary bundles, apps, libs, and services that aren't needed by
    the activated_bundles.  It also expands inside specs.apps.depends.libs all libs that are needed
    indirectly by each app
    """
    _filter_active(constants.CONFIG_BUNDLES_KEY, specs)
    _filter_active('apps', specs)
    _expand_libs_in_apps(specs)
    _filter_active('libs', specs)
    _filter_active('services', specs)
    _add_active_assets(specs)

def _get_expanded_libs_specs(specs):
    _expand_libs_in_apps(specs)
    _expand_libs_in_libs(specs)

@memoized
def get_assembled_specs():
    logging.debug("Spec Assembler: running...")
    specs = get_specs()
    _get_expanded_active_specs(specs)
    return specs

def get_expanded_libs_specs():
    specs = get_specs()
    _get_expanded_libs_specs(specs)
    return specs

def get_specs_repo():
    return Repo(get_config_value(constants.CONFIG_SPECS_REPO_KEY))

def get_specs_path():
    return get_specs_repo().local_path

@memoized
def get_specs():
    specs_path = get_specs_path()
    return get_specs_from_path(specs_path)

def get_repo_of_app_or_library(app_or_library_name):
    """ This function takes an app or library name and will return the corresponding repo
    for that app or library"""
    specs = get_specs()
    repo_name = specs.get_app_or_lib(app_or_library_name)['repo']
    if not repo_name:
        return None
    return Repo(repo_name)

def get_specs_from_path(specs_path):
    return DustySpecs(specs_path)

def get_all_repos(active_only=False, include_specs_repo=True):
    repos = set()
    if include_specs_repo:
        repos.add(get_specs_repo())
    specs = get_assembled_specs() if active_only else get_specs()
    for spec in specs.get_apps_and_libs():
        if spec['repo']:
            repos.add(Repo(spec['repo']))
    return repos

def get_same_container_repos_from_spec(app_or_library_spec):
    """Given the spec of an app or library, returns all repos that are guaranteed
    to live in the same container"""
    repos = set()
    app_or_lib_repo = get_repo_of_app_or_library(app_or_library_spec.name)
    if app_or_lib_repo is not None:
        repos.add(app_or_lib_repo)
    for dependent_name in app_or_library_spec['depends']['libs']:
        repos.add(get_repo_of_app_or_library(dependent_name))
    return repos

def get_same_container_repos(app_or_library_name):
    """Given the name of an app or library, returns all repos that are guaranteed
    to live in the same container"""
    specs = get_expanded_libs_specs()
    spec = specs.get_app_or_lib(app_or_library_name)
    return get_same_container_repos_from_spec(spec)
