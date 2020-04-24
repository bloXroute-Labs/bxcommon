# pylint: disable=global-statement

import configparser
import json
import multiprocessing
import os
import re
import shutil
import sys
from os import path
from pathlib import Path
from typing import Dict, Any

from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxutils import logging

logger = logging.get_logger(__name__)

_working_directory = ""
_data_directory = ""


def set_working_directory(working_directory: str):
    """
    Sets working directory of python application
    :param working_directory: full name of working directory
    """
    global _working_directory
    _working_directory = working_directory


def set_data_directory(data_directory: str):
    """
    Sets the directory where configuration, state and log files are being stored
    :param data_directory: full name of data directory
    """
    global _data_directory
    _data_directory = data_directory
    try:
        os.makedirs(data_directory, exist_ok=True)

    # pylint: disable=broad-except
    except Exception as e:
        logger.fatal(
            "Unable to create data directory '{}'. Error: {}. Exiting.",
            data_directory,
            e
        )
        sys.exit(1)


def get_default_data_path():
    """
    Returns default data directory for configuration, state and log files
    :return: default data directory
    """

    if sys.platform == constants.PLATFORM_MAC:
        return path.join(get_home_path(), "Library", "bloXroute")
    else:
        return path.join(get_home_path(), "bloxroute")


def get_home_path():
    """
    Returns user home directory
    :return: home directory
    """
    return str(Path.home())


def get_relative_file(file_path: str) -> str:
    return os.path.join(_working_directory, file_path)


def get_data_file(file_path: str) -> str:
    return os.path.join(_data_directory, file_path)


def log_pid(file_name):
    """
    Capture process id for easy termination in multi-thread scenarios.
    """
    with open(file_name, "w") as writable_file:
        writable_file.write(str(os.getpid()))


def get_env_default(key: str) -> str:
    """
    Read the default values for given key from the config file for a specific environment. The environment is stored
    in the hosts environment variables as `BLXR_ENV=local` for example. If the environment isn't set or doesn't exist
    in the config file, the global default values are returned

    :param key: the key to get the env default values for
    :return: the env default value
    """
    config = configparser.ConfigParser()
    config_file_path = get_relative_file(constants.NODE_CONFIG_FILE)
    config.read(config_file_path)

    # If the environment var itself does not exist, return the global default value for the key
    if constants.BLXR_ENV_VAR not in os.environ:
        return config.defaults()[key]

    environment = os.environ[constants.BLXR_ENV_VAR].lower()

    # If the given environment var does not have an entry in the config file, return the global default
    if environment in config.sections():
        return config.get(environment, key)
    else:
        return config.defaults()[key]


def get_thread_pool_parallelism_degree(parallelism_degree_str: str) -> int:
    parallelism_degree = int(parallelism_degree_str)
    if parallelism_degree <= 0:
        parallelism_degree = 1
    return min(
        parallelism_degree,
        max(multiprocessing.cpu_count() - 1, 1)
    )


def is_valid_version(full_version: str) -> bool:
    """
    check if version number in template: {int}.{int}.{int}.{int} and version type is dev/ci/v
    :param full_version: {version_type}{version_number}
    :return: if the version is valid
    """
    index = re.search(r"\d", full_version)
    if index is None:
        raise ValueError(f"Version is incorrectly formated: {full_version}")
    index = index.start()

    version_number = full_version[index:]
    version_type = full_version[:index]
    return (version_number.count(".") == 3 and all(str(x).isdigit() for x in version_number.split("."))) and \
           (version_type in constants.VERSION_TYPE_LIST)


def read_manifest(manifest_path: str) -> Dict[str, str]:
    """
    Reads manifest file, ensuring that manifest contains all expected properties.
    :param manifest_path:
    :return: manifest
    """
    try:
        with open(manifest_path, "r") as json_file:
            manifest = json.load(json_file)
            version = manifest[constants.MANIFEST_SOURCE_VERSION]

            if not is_valid_version(version):
                raise ValueError(f"Invalid version: {version}")

            if not all(params in manifest for params in constants.REQUIRED_PARAMS_IN_MANIFEST):
                missing_params_str = ", ".join(
                    [item for item in constants.REQUIRED_PARAMS_IN_MANIFEST if item not in manifest])
                raise ValueError(f"Missing attributes: {missing_params_str}")

            return manifest
    except Exception as e:
        raise Exception(f"Unexpected error while reading manifest file at: {manifest_path}. Error: {e}")


def append_manifest_args(opts_dict: Dict[Any, Any]):
    manifest_path = get_relative_file(constants.MANIFEST_PATH)
    manifest = read_manifest(manifest_path)
    opts_dict.update(manifest)
    opts_dict.update({constants.PROTOCOL_VERSION: bloxroute_version_manager.CURRENT_PROTOCOL_VERSION})


def init_file_in_data_dir(file_name: str):
    relative_file_name = get_relative_file(file_name)
    data_dir_file_name = get_data_file(file_name)

    if os.path.exists(relative_file_name) and not os.path.exists(data_dir_file_name):
        shutil.copyfile(relative_file_name, data_dir_file_name)
