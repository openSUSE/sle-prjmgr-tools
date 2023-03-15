"""
Module to serve the version output of the tool.
"""

from argparse import Namespace

import sle_prjmgr_tools


def build_parser(parent_parser):
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.
    """
    subparser = parent_parser.add_parser(
        "version", help="Shows the version of the tool that is used."
    )
    subparser.set_defaults(func=main_cli)


def main_cli(args: Namespace) -> None:  # pylint: disable=unused-argument
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    print(sle_prjmgr_tools.__version__)
