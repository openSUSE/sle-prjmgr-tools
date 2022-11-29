"""
Get all JIRA Issues that are mentioned in the changelog of a project.
"""
import re
from typing import Dict, List

from lxml import etree
from osc import core, conf  # type: ignore


def build_parser(parent_parser):
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.

    :param parent_parser: The subparsers object from argparse.
    """
    subparser = parent_parser.add_parser("jira_epics", help="jira_epics help")
    subparser.add_argument(
        "--target",
        "-t",
        dest="target",
        default="SUSE:SLE-15-SP5:GA",
        help="Project to execute against.",
    )
    subparser.set_defaults(func=main_cli)


def osc_prepare():
    """
    This has to be executed to the ini-style config is converted into their corresponding types.
    """
    conf.get_config()


def osc_packages_exclude_000(apiurl: str, target: str) -> List[str]:
    """
    Retrieve a list of packages for a given project where all packages starting with ``000`` are being excluded.

    :param apiurl: URL where the API from the build-service can be reached.
    :param target: The target project to search.
    :return: The list of packages in the project.
    """
    result = []
    for package in core.meta_get_packagelist(apiurl, target):
        if not package.startswith("000"):
            result.append(package)
    return result


def get_issue_list(apiurl: str, target: str, package: str) -> List[str]:
    """
    Scans the changelog for a specific package for jsc mentions.

    :param apiurl: URL where the API from the build-service can be reached.
    :param target: The target project that this is checked against.
    :param package: The package that should be scanned for issues.
    :return: The list of issues that could be found.
    """
    baseurl = ["source", target, package]
    query = {"cmd": "diff", "view": "xml", "onlyissues": "1", "orev": "1"}
    url = core.makeurl(apiurl, baseurl, query)
    fp_post_result = core.http_POST(url)
    xml_issues = etree.parse(fp_post_result).getroot()
    issue_list_xml = xml_issues.xpath(
        '//sourcediff/issues/issue[@state="added"][@tracker="jsc"]'
    )
    issue_list = []
    for issue in issue_list_xml:
        issue_list.append(issue.get("label"))
    return issue_list


def scan_commitlog_for_issues(apiurl: str, target: str, package: str) -> List[str]:
    """
    Scans the commitlog for a specific package for jsc mentions.

    :param apiurl: URL where the API from the build-service can be reached.
    :param target: The target project that this is checked against.
    :param package: The package that should be scanned for issues.
    :return: The list of issues that could be found.
    """
    issue_list = []
    jsc_regex = re.compile(r"jsc#[a-zA-Z]*-\d*")
    xml_str_commitlog = "\n".join(
        core.get_commitlog(
            apiurl, target, package, None, format="xml", revision_upper=None
        )
    )
    tree = etree.fromstring(xml_str_commitlog)
    msgs = tree.xpath("//msg")
    for msg in msgs:
        matches = jsc_regex.findall(msg.text)
        if len(matches) > 0:
            issue_list.extend(matches)
    return issue_list


def main(
    apiurl="https://api.suse.de", target="SUSE:SLE-15-SP3:GA"
) -> Dict[str, List[str]]:
    """
    Main routine executes the non-CLI related logic.

    :param apiurl: URL where the API from the build-service can be reached.
    :param target: The target project that this is checked against.
    """
    osc_prepare()
    result: Dict[str, List[str]] = {}
    for package in osc_packages_exclude_000(apiurl, target):
        issue_list = get_issue_list(apiurl, target, package)
        issue_list.extend(scan_commitlog_for_issues(apiurl, target, package))
        result[package] = issue_list
    return result


def main_cli(args):
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    data = main(apiurl=args.osc_instance, target=args.target)
    for package, issue_list in data.items():
        if len(issue_list) > 0:
            print(package)
            for issue in issue_list:
                print(issue)
        else:
            print(f"{package} - No jscs mentioned")
