"""
This script calculates a diff between two project revisions and writes its output to a file where the added, moved and
removed packages are named.
"""

import logging
import shlex
import subprocess
import sys
import textwrap
from typing import Dict, List, Optional

import yaml


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def build_parser(parent_parser):
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.

    :param parent_parser: The subparsers object from argparse.
    """
    subparser = parent_parser.add_parser(
        "packagelist_report", help="Report of package movements between 2 projects"
    )
    subparser.add_argument(
        "-f", "--from-project", type=str, help="Origin project", required=True
    )
    subparser.add_argument(
        "-t", "--to-project", type=str, help="Target project", required=True
    )
    subparser.add_argument(
        "--from-revision-number", type=str, help="Origin revision number"
    )
    subparser.add_argument(
        "--to-revision-number", type=str, help="Target revision number"
    )
    subparser.set_defaults(func=main_cli)


def convert_txt_to_dict(file_content: str) -> Dict[str, List[str]]:
    """
    Converts the text file downloaded and parses

    :param file_content: The string that should be split
    :return: The dictionary with the package names as key and the list of groups they are in as a list.
    """
    ret: Dict[str, List[str]] = {}
    for line in file_content.splitlines():
        pkg, group = line.strip().split(":")
        ret.setdefault(pkg, [])
        ret[pkg].append(group)
    return ret


def convert_yml_to_dict(file_content: str, unsorted=False) -> Dict[str, List[str]]:
    """
    Loads the file content as a YAML file and then parses it according to the expected file structure.

    :param file_content: The content of the YAML file.
    :param unsorted: If the package should be added to unsorted or not explicitly.
    :return: The dictionary with the package names as key and the list of groups they are in as a list.
    """
    ret: Dict[str, List[str]] = {}
    try:
        parsed_yaml = yaml.safe_load(file_content)
        for module, packages in parsed_yaml.items():
            for package in packages:
                if unsorted:
                    ret[package] = ["unsorted"]
                else:
                    ret[package] = [module]
    except yaml.YAMLError as yaml_error:
        logger.error(yaml_error, exc_info=True)
    return ret


def download_file(cmd: str):
    """
    Takes an osc command returns the stdout.

    :param cmd: The osc command to run.
    :return: The stdout output.
    """
    logger.debug("Executing: %s", cmd)
    cmd_args = shlex.split(cmd)
    output = subprocess.run(cmd_args, capture_output=True, text=True, check=False)
    if output.returncode != 0:
        logger.warning("Failed to execute: %s", cmd)
        logger.warning(output.stderr)
    return output


def get_yml_files(command: str, revision) -> Optional[Dict[str, List[str]]]:
    """
    Retrieve the different reference YAML files and parse them.

    :param command: The pre-built command that should be used.
    :param revision: The project revision to get the file from.
    :return: The dictionary with the package names as key and the list of groups they are in as a list.
    """
    ret: Dict[str, List[str]] = {}
    yaml_files = ["reference-summary.yml", "reference-unsorted.yml", "unneeded.yml"]
    for file in yaml_files:
        cmd = command + f" {file}"
        if revision:
            cmd += f" -r {revision}"
        output = download_file(cmd)
        if output.returncode != 0:
            return None
        unsorted_flag = file != yaml_files[0]
        content = convert_yml_to_dict(output.stdout, unsorted_flag)
        ret = {**ret, **content}
    return ret


def get_txt_file(cmd: str, revision) -> Optional[Dict[str, List[str]]]:
    """
    Retrieve and parse the content of ``summary-staging.txt``.

    :param cmd: The pre-built command that should be used.
    :param revision: The project revision to get the file from.
    :return: The file that has been downloaded by osc and then parsed by ``convert_txt_to_dict()``.
    """
    file = "summary-staging.txt"
    cmd += f" {file}"
    if revision:
        cmd += f" -r {revision}"
    output = download_file(cmd)
    if output.returncode != 0:
        return None
    return convert_txt_to_dict(output.stdout)


def get_file_content(project: str, revision: str):
    """
    Retrieves the file content of a text file from 000package-groups.

    :param project: The project that should be checked.
    :param revision: The project revision to get the file from.
    :return: The
    """
    apiurl = "https://api.suse.de/"
    package = "000package-groups"
    cmd = f"osc -A {apiurl} cat {project} {package}"
    ret = get_txt_file(cmd, revision)
    if not ret:
        ret = get_yml_files(cmd, revision)
        if not ret:
            sys.exit(1)
    write_summary_dict(project, ret)
    return ret


def read_yaml_file(file, unsorted=False):
    """
    Loads the file content as a YAML file and then parses it according to the expected file structure.

    :param file: The content of the YAML file.
    :param unsorted: If the package should be added to unsorted or not explicitly.
    :return: The dictionary with the package names as key and the list of groups they are in as a list.
    """
    ret = {}
    with open(file, "r", encoding="UTF-8") as stream:
        try:
            parsed_yaml = yaml.safe_load(stream)
            for module, packages in parsed_yaml.items():
                for package in packages:
                    if unsorted:
                        ret[package] = ["unsorted"]
                    else:
                        ret[package] = [module]
        except yaml.YAMLError as yaml_error:
            logger.error(yaml_error, exc_info=True)
    return ret


def read_summary_file(file: str) -> Dict[str, List[str]]:
    """
    Reads a file and interprets it in the format of ``summary-staging.txt``.

    :param file: The path to the file.
    :return: The dict with the package names as keys and the list of groups as a value.
    """
    ret: Dict[str, List[str]] = {}
    with open(file, "r", encoding="UTF-8") as fp_summary_file:
        for line in fp_summary_file:
            pkg, group = line.strip().split(":")
            ret.setdefault(pkg, [])
            ret[pkg].append(group)
    return ret


def write_summary_file(file: str, content: str) -> None:
    """
    Write a file to disk with the given content.

    :param file: The file path of the desired target.
    :param content: The content to write.
    """
    logger.info("Summary report saved in %s", file)
    with open(file, "w", encoding="UTF-8") as fp_summary_file:
        fp_summary_file.write(content)


def write_summary_dict(file: str, content: Dict[str, List[str]]) -> None:
    """
    Write a file to disk with the given content.

    :param file: The file path of the desired target.
    :param content: The dict with the packages as keys and their categories as value.
    """
    logger.info("List of %s packages saved in %s", file, file)
    output = []
    for pkg in sorted(content):
        for group in sorted(content[pkg]):
            output.append(f"{pkg}:{group}")

    with open(file, "w", encoding="UTF-8") as fp_summary_file:
        for line in sorted(output):
            fp_summary_file.write(line + "\n")


def generate_package_diff_report(added: dict, moved: dict, removed: dict) -> str:
    """
    Generates the report with the help of the presorted dictionaries.

    :param added: The dict with added packages
    :param moved: The dict with moved packages
    :param removed: The dict with removed packages
    :return: The str with the generated report. Newlines for formatting are present.
    """
    report = ""
    for removed_package in sorted(removed.keys()):
        report += f"**Remove from {removed_package}**\n\n```\n"
        paragraph = ", ".join(removed[removed_package])
        report += "\n".join(
            textwrap.wrap(
                paragraph, width=90, break_long_words=False, break_on_hyphens=False
            )
        )
        report += "\n```\n\n"

    for move in sorted(moved.keys()):
        report += f"**Move from {move}**\n\n```\n"
        paragraph = ", ".join(moved[move])
        report += "\n".join(
            textwrap.wrap(
                paragraph, width=90, break_long_words=False, break_on_hyphens=False
            )
        )
        report += "\n```\n\n"

    for group in sorted(added):
        report += f"**Add to {group}**\n\n```\n"
        paragraph = ", ".join(added[group])
        report += "\n".join(
            textwrap.wrap(
                paragraph, width=90, break_long_words=False, break_on_hyphens=False
            )
        )
        report += "\n```\n\n"

    return report.strip()


def calculcate_package_diff(old_file: dict, new_file: dict) -> Optional[str]:
    """
    Calculate the package diff between the two dictionaries that were passed.

    :param old_file: Dictionary with the content from the source project.
    :param new_file: Dictionary with the content from the target project.
    :return: The str with the generated report. As generated by ``generate_package_diff_report()``.
    """
    # remove common part
    keys = list(old_file.keys())
    for key in keys:
        if new_file.get(key, []) == old_file[key]:
            del new_file[key]
            del old_file[key]

    if not old_file and not new_file:
        return None

    added: Dict[str, List[str]] = {}
    for pkg in new_file:
        if pkg in old_file:
            continue
        addkey = ",".join(new_file[pkg])
        added.setdefault(addkey, [])
        added[addkey].append(pkg)

    removed: Dict[str, List[str]] = {}
    for pkg in old_file:
        old_groups = old_file[pkg]
        if new_file.get(pkg):
            continue
        removekey = ",".join(old_groups)
        removed.setdefault(removekey, [])
        removed[removekey].append(pkg)

    moved: Dict[str, List[str]] = {}
    for pkg in old_file:
        old_groups = old_file[pkg]
        new_groups = new_file.get(pkg)
        if not new_groups:
            continue
        movekey = ",".join(old_groups) + " to " + ",".join(new_groups)
        moved.setdefault(movekey, [])
        moved[movekey].append(pkg)

    return generate_package_diff_report(added, moved, removed)


def main(
    from_project: str,
    from_revision_number: str,
    to_project: str,
    to_revision_number: str,
):
    """
    Main routine executes the non-CLI related logic.

    :param from_project: Source project that should be used as a base.
    :param from_revision_number: Project revision number.
    :param to_project: Source project that should be used as a comparison target.
    :param to_revision_number: Project revision number.
    """
    from_summary = get_file_content(from_project, from_revision_number)
    to_summary = get_file_content(to_project, to_revision_number)
    report = calculcate_package_diff(from_summary, to_summary)
    # logger.debug(f"\n{report}")
    logger.debug("\n%s", from_revision_number)
    logger.debug("\n%s", to_revision_number)
    if report:
        summary_file = "summary-report.md"
        write_summary_file(summary_file, report)
    else:
        logger.info("No package movement reported")

    # if os.path.isfile(reference_summary):
    # from_shipped = read_yaml_file(f'FROM-shipped.yml')
    # from_unsorted = read_yaml_file(f'FROM-unsorted.yml',True)
    # from_summary = {**from_shipped, **from_unsorted}
    # from_summary_file = f'from_summary-external'
    # write_summary_dict(from_summary_file, from_summary)

    # to_summary = read_summary_file(f'TO-summary-staging.txt')
    # to_summary_file = f'to_summary-external'
    # write_summary_dict(to_summary_file, to_summary)

    # report = calculcate_package_diff(from_summary, to_summary)
    # logger.debug(f"\n{report}")
    # summary_file = f'diff-report-external.md'
    # write_summary_file(summary_file, report)


def main_cli(args):
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    main(
        args.from_project,
        args.from_revision_number,
        args.to_project,
        args.to_revision_number,
    )
