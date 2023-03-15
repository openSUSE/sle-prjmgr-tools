"""
Configuration related package.
"""

import json
import logging
import os
import traceback
from typing import List

from importlib_resources import files


CONFIG_LOCATIONS = [
    "/etc/sle-prjmgr-tools.json",
    "$XDG_CONFIG_HOME/sle-prjmgr-tools.json",
    "$RELEASE_MANAGEMENT_TOOLS_FILE",
]

logger = logging.getLogger()


def load_modules() -> List[str]:
    """
    Method that loads all modules from the config and returns them to the application.
    """
    module_list = []
    config_found = False
    for location in CONFIG_LOCATIONS:
        if "$" in location:
            real_location = os.path.expandvars(location)
        else:
            real_location = location
        if os.path.isfile(real_location):
            module_list = load_config(real_location)
            config_found = True
        else:
            logger.debug('"%s" was skipped.', real_location)
    if not config_found:
        backup_config_path = str(
            files("sle_prjmgr_tools.config").joinpath("sle-prjmgr-tools.json")
        )
        module_list = load_config(backup_config_path)
        logger.debug("Built-In Configuration was used!")
    return module_list


def load_config(path: str) -> List[str]:
    """
    Loads the JSON config file.

    :param path: This path is excepted to exist. It should be the absolute path to the config file.
    :return: The list of modules that should be loaded.
    """
    with open(path, "rt", encoding="UTF-8") as json_fp:
        try:
            json_dict = json.load(json_fp)
            logger.debug('JSON config loaded from "%s".', path)
            return json_dict.get("modules")
        except json.JSONDecodeError:
            logger.debug("JSON syntax error! Fix syntax to load modules.")
            traceback.print_exc()
            return []
