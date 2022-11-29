"""
Module that will release a ``:GA`` project to ``:GA:TEST``.
"""
from typing import Optional

from sle_prjmgr_tools.utils.osc import OscReleaseHelper


def build_parser(parent_parser):
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.

    :param parent_parser: The subparsers object from argparse.
    """
    # pylint: disable=R0801
    subparser = parent_parser.add_parser("release_to_test", help="release_to_test help")
    subparser.add_argument(
        "project",
        metavar="project",
        help="Project that should be released including the GA suffix.",
    )


def main(obs_url: str, project: str, osc_config: Optional[str] = None):
    """
    Main routine executes the non-CLI related logic.

    :param obs_url: URL to the OBS instance.
    :param project: Project to release. Must include the ``:GA`` suffix but not more.
    :param osc_config: Path to the ``.oscrc``. It may be ``None`` if osc should handle the lookup.
    """
    releaser = OscReleaseHelper(osc_server=obs_url, override_config=osc_config)
    releaser.release_repo_to_test(project)


def main_cli(args):
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    main(args.osc_instance, args.project, args.osc_config)
