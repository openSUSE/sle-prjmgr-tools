"""
Module that will release a ``:GA`` project to ``:GA:TEST`` or ``GA:PUBLISH``.
"""
import enum
from typing import Optional

from sle_prjmgr_tools.utils.osc import OscReleaseHelper


class ReleaseTargets(enum.Enum):
    """
    This Enum contains all possible release targets for this script.
    """

    TEST = 0
    PUBLISH = 1


def build_parser(parent_parser):
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.

    :param parent_parser: The subparsers object from argparse.
    """
    # pylint: disable=R0801
    subparser = parent_parser.add_parser("release_to", help="release_to help")
    group = subparser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--test",
        dest="release_target",
        action="store_const",
        const=ReleaseTargets.TEST,
        help="If this flag is given, a release to :GA:TEST is triggered.",
    )
    group.add_argument(
        "--publish",
        dest="release_target",
        action="store_const",
        const=ReleaseTargets.PUBLISH,
        help="If this flag is given, a release to :GA:PUBLISH is triggered.",
    )
    subparser.add_argument(
        "project",
        metavar="project",
        help="Project that should be released including the GA suffix.",
    )


def main(
    obs_url: str, project: str, target: ReleaseTargets, osc_config: Optional[str] = None
):
    """
    Main routine executes the non-CLI related logic.

    :param obs_url: URL to the OBS instance.
    :param project: Project to release. Must include the ``:GA`` suffix but not more.
    :param target: Decides what the release target is.
    :param osc_config: Path to the ``.oscrc``. It may be ``None`` if osc should handle the lookup.
    """
    releaser = OscReleaseHelper(osc_server=obs_url, override_config=osc_config)
    if target == ReleaseTargets.TEST:
        releaser.release_repo_to_test(project)
    elif target == ReleaseTargets.PUBLISH:
        releaser.release_repo_to_publish(project)


def main_cli(args):
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    main(args.osc_instance, args.project, args.release_target, args.osc_config)
