"""
Script to diff two well-known modules with each another.
"""

import argparse
import pathlib
import subprocess
from collections import namedtuple
from typing import Optional

from sle_prjmgr_tools.utils.osc import OscUtils


DiffModuleOptions = namedtuple("DiffModuleOptions", "project revision")
OscOptions = namedtuple("OscOptions", "config instance")


def build_parser(parent_parser):
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.

    :param parent_parser: The subparsers object from argparse.
    """
    subparser = parent_parser.add_parser("diff_modules", help="diff_modules help")
    subparser.add_argument(
        "-f",
        "--from-project",
        dest="from_project",
        default="15-SP4",
        help='The source project. Should be in the form "15-SP4".',
    )
    subparser.add_argument(
        "-o",
        "--from-revision-number",
        dest="from_revision_number",
        help='The revision number of the "groups.yml" file in the source project.',
    )
    subparser.add_argument(
        "-t",
        "--to-project",
        dest="to_project",
        default="15-SP5",
        help='The source project. Should be in the form "15-SP4".',
    )
    subparser.add_argument(
        "-d",
        "--to-revision-number",
        dest="to_revision_number",
        help='The revision number of the "groups.yml" file in the target project.',
    )
    subparser.add_argument(
        "--output-file",
        dest="output_file",
        type=argparse.FileType("w+", encoding="UTF-8"),
        help="If the argument is present the result is written to the file specified in the argument, otherwise result"
        "is printed to stdout.",
    )
    subparser.set_defaults(func=main_cli)


def checkout_source_files(
    from_project: DiffModuleOptions,
    to_project: DiffModuleOptions,
    from_groups_filename: pathlib.Path,
    to_groups_filename: pathlib.Path,
    osc_config: Optional[OscOptions] = None,
):
    """
    Download the two "group.yml" files from "000package-groups" that will be compared.

    :param from_project: The project the source package is in.
    :param to_project: The project the target package is in.
    :param from_groups_filename: The desired filename for the source file.
    :param to_groups_filename: The desired filename for the target file.
    :param osc_config: The tuple with the osc options.
    """
    if osc_config is None:
        my_utils = OscUtils()
    else:
        my_utils = OscUtils(
            osc_server=osc_config.instance, override_config=osc_config.config
        )
    my_utils.get_file_from_package(
        from_project.project,
        "000package-groups",
        from_project.revision,
        "groups.yml",
        target_filename=str(from_groups_filename),
    )
    my_utils.get_file_from_package(
        to_project.project,
        "000package-groups",
        to_project.revision,
        "groups.yml",
        target_filename=str(to_groups_filename),
    )


def run_sed(expression: str, file: pathlib.Path):
    """
    Runs the given sed Expression on a specified file.

    :param expression: The sed expression.
    :param file: The file that should be used.
    """
    subprocess.run(["sed", "-i", "-e", expression, str(file)], check=False)


def cleanup_source_files(
    from_groups_filename: pathlib.Path, to_groups_filename: pathlib.Path
):
    """
    Removes the temporary files.

    :param from_groups_filename: The file that acts as a source for the comparison.
    :param to_groups_filename: The file that acts as a target for the comparison.
    """
    from_groups_filename.unlink()
    to_groups_filename.unlink()


def remove_comments(from_groups: pathlib.Path, to_groups: pathlib.Path):
    """
    Remove all comments from the two files.

    :param from_groups: The source file that should be modified.
    :param to_groups: The target file that should be modified.
    """
    expression = r"s/\s*#.*$//"
    run_sed(expression, from_groups)
    run_sed(expression, to_groups)


def output_mark_packages_in_to_file(to_groups: pathlib.Path):
    """
    Mark all package in the target file.

    :param to_groups: The file that should be modified.
    """
    run_sed(r"s/\(^[a-zA-Z_]*:$\)/ \1/g", to_groups)


def diff_file(
    from_groups: pathlib.Path, to_groups: pathlib.Path, changes_file: pathlib.Path
):
    """
    Diff the two files and write it to the third file.

    :param from_groups: The source file that should be modified.
    :param to_groups: The target file that should be modified.
    :param changes_file: The file with the resulting changes.
    """
    with changes_file.open("w") as changes_file_fp:
        subprocess.run(
            [
                "diff",
                "--suppress-common-lines",
                "--ignore-blank-lines",
                "--ignore-trailing-space",
                str(from_groups),
                str(to_groups),
            ],
            stdout=changes_file_fp,
            check=False,
        )


def output_remove_line_numbers(changes_file: pathlib.Path):
    """
    Remove all line numbers from the file.

    :param changes_file: The file that should be modified.
    """
    run_sed(r"/^[0-9].*$/d", changes_file)


def output_remove_dashes(changes_file: pathlib.Path):
    """
    Remove all dashes from the diff.

    :param changes_file: The file that should be modified.
    """
    run_sed(r"/^---$/d", changes_file)


def output_remove_repeated_module_names(changes_file: pathlib.Path):
    """
    Remove all repeated module names from the diff.

    :param changes_file: The file that should be modified.
    """
    run_sed(r"/< [a-zA-Z_]*:$/d", changes_file)


def output_remove_empty_lines(changes_file: pathlib.Path):
    """
    Remove all empty lines from the diff.

    :param changes_file: The file that should be modified.
    """
    run_sed(r"/^[<>]\s*$/d", changes_file)


def output_mark_removed_packages(changes_file: pathlib.Path):
    """
    Mark all packages that are removed.

    :param changes_file: The file that should be modified.
    """
    run_sed(r"s/^<\s*-/-  /", changes_file)


def output_mark_added_packages(changes_file: pathlib.Path):
    """
    Mark all packages that are added.

    :param changes_file: The file that should be modified.
    """
    run_sed(r"s/^>\s*-/+  /", changes_file)


def output_removed_from_module_names(changes_file: pathlib.Path):
    """
    Mark packages that are removed from a module.

    :param changes_file: The file that should be modified.
    """
    run_sed(r"s/^[<>]\s\s//", changes_file)


def output_remove_unrelated_to_modules(changes_file: pathlib.Path):
    """
    Remove all packages that are unrelated to modules.

    :param changes_file: The file that should be modified.
    """
    run_sed(r"/^UNWANTED:/,$!d", changes_file)


def main(
    from_project: DiffModuleOptions,
    to_project: DiffModuleOptions,
    osc_config: Optional[OscOptions] = None,
) -> str:
    """
    Main routine executes the non-CLI related logic.

    :param from_project: The source project that should be compared.
    :param to_project: The target project that should be compared.
    :param osc_config: The osc configuration that should be used.
    """
    from_groups_file = pathlib.Path("groups_FROM.yml")
    to_groups_file = pathlib.Path("groups_TO.yml")
    changes_groups_file = pathlib.Path(
        f"Changes_from_{from_project}_to_{to_project}.diff"
    )
    from_project = DiffModuleOptions(
        f"SUSE:SLE-{from_project.project}:GA", from_project.revision
    )
    to_project = DiffModuleOptions(
        f"SUSE:SLE-{to_project.project}:GA", to_project.revision
    )

    checkout_source_files(
        from_project,
        to_project,
        from_groups_file,
        to_groups_file,
        osc_config=osc_config,
    )
    remove_comments(from_groups_file, to_groups_file)
    output_mark_packages_in_to_file(to_groups_file)
    diff_file(from_groups_file, to_groups_file, changes_groups_file)
    cleanup_source_files(from_groups_file, to_groups_file)
    output_remove_line_numbers(changes_groups_file)
    output_remove_dashes(changes_groups_file)
    output_remove_repeated_module_names(changes_groups_file)
    output_remove_empty_lines(changes_groups_file)
    output_mark_removed_packages(changes_groups_file)
    output_mark_added_packages(changes_groups_file)
    output_removed_from_module_names(changes_groups_file)
    output_remove_unrelated_to_modules(changes_groups_file)
    result = changes_groups_file.read_text(encoding="UTF-8")
    changes_groups_file.unlink()
    return result


def main_cli(args):
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    result = main(
        DiffModuleOptions(args.from_project, args.from_revision_number),
        DiffModuleOptions(args.to_project, args.to_revision_number),
        osc_config=OscOptions(args.osc_config, args.osc_instance),
    )
    if args.output_file:
        with args.output_file as output_file_fp:
            output_file_fp.write(result)
    else:
        print(result)
