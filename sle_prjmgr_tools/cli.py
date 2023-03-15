# PYTHON_ARGCOMPLETE_OK
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
import logging
import sys
import urllib.error

import argcomplete  # type: ignore

from sle_prjmgr_tools import config


PARSER = argparse.ArgumentParser(
    prog="sle_prjmgr_tools", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
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
SUBPARSERS = PARSER.add_subparsers(
    help="Help for the subprograms that this tool offers."
)
logger = logging.getLogger()


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
    import_plugin("version")
    module_list = config.load_modules()
    for module in module_list:
        import_plugin(module)
    argcomplete.autocomplete(PARSER)
    args = PARSER.parse_args()
    if "func" in vars(args):
        # Run a subprogramm only if the parser detected it correctly.
        try:
            args.func(args)
        except urllib.error.URLError as url_error:
            if "name or service not known" in str(url_error).lower():
                print(
                    "No connection to one of the tools. Please make sure the connection to the tools is available"
                    " before executing the program!"
                )
                sys.exit(1)
        return
    PARSER.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
