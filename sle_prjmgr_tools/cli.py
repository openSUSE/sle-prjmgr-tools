"""
This is the wrapper script that specifies the CLI entry point that can load the scripts from a config file.

The config file has the following format: { "modules": [ "module1", "module2" ] }

Valid locations for the configuration file are:

- "/etc/sle-prjmgr-tools.json"
- "$XDG_CONFIG_HOME/sle-prjmgr-tools.json"
- "$RELEASE_MANAGEMENT_TOOLS_FILE"

A module must have a "build_parser" method that takes a single argument. The method is responsible to assign with
"set_default" the func kwarg. The CLI entrypoint is called "main_cli" and has a single arguments that is an argparse
namespace. This should be just a wrapper to the "main" function that has the actual arguments defined.

If no config is supplied the built-in configuration is used.

Example usage of the CLI for development (from git project root):

  > . venv/bin/activate
  > export RELEASE_MANAGEMENT_TOOLS_FILE="config/sle-prjmgr-tools.json"
  > python3 -m sle_prjmgr_tools.cli -h
"""
import argparse
import importlib
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
PARSER = argparse.ArgumentParser(prog="sle_prjmgr_tools")
PARSER.add_argument(
    "--osc-config",
    dest="osc_config",
    help="The location of the oscrc if a specific one should be used.",
)
PARSER.add_argument(
    "--osc-instance",
    dest="osc_instance",
    help="The URL of the API from the Open Buildservice instance that should be used.",
    default="https://api.suse.de",
)
PARSER.add_argument(
    "--jira-instance",
    dest="jira_instance",
    help="The URL for the JIRA instance.",
    default="https://jira.suse.com",
)
PARSER.add_argument(
    "--confluence-instance",
    dest="confluence_instance",
    help="The URL for the Confluence instance.",
    default="https://confluence.suse.com",
)
SUBPARSERS = PARSER.add_subparsers(help="Help for the actual scripts")
logger = logging.getLogger()


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


def import_plugin(name: str):
    """
    This method imports a plugin

    :param name: The name of the module in the "sle_prjmgr_tools" module.
    """
    plugin = importlib.import_module(f".{name}", package="sle_prjmgr_tools")
    plugin.build_parser(SUBPARSERS)


def main():
    """
    The main entrypoint for the library.
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
    for module in module_list:
        import_plugin(module)
    args = PARSER.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
