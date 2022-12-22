"""
This script retrieves all updates to packages between two builds.
"""
import re
from collections import namedtuple
from typing import Dict, List, Set

import requests


def build_parser(parent_parser):
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.

    :return: The subparsers object from argparse.
    """
    subparser = parent_parser.add_parser(
        "package_updates_from_xcdchk", help="package_updates_from_xcdchk help"
    )
    subparser.add_argument(
        "-A",
        "--xcdchk-timeout",
        dest="xcdchk_timeout",
        type=int,
        default=60,
        help="The xcdchk timeout after which the request will be aborted.",
    )
    subparser.add_argument(
        "-a",
        "--xcdchk-url",
        dest="xcdchk_url",
        default="http://xcdchk.suse.de",
        help="The xcdchk Domain.",
    )
    subparser.add_argument(
        "-b",
        "--build",
        dest="builds",
        type=float,
        nargs=2,
        required=True,
        help="The build numbers that should be compared.",
    )
    subparser.add_argument(
        "--service-pack",
        dest="service_pack",
        default="SLE-15-SP5",
        help='The service pack in the form of "SLE-15-SPx".',
    )
    subparser.add_argument(
        "--origin-service-pack",
        dest="origin_service_pack",
        default="SLE-15-SP5",
        help='The service pack in the form of "SLE-15-SPx".',
    )
    subparser.set_defaults(func=main_cli)


class XcdChkUpdatedPackageVersion:
    """
    This class is responsible for holding the package versions.
    """

    # Disabled because dataclasses are not a thing in Python 3.6
    # pylint: disable=R0903

    def __init__(self, old_version="", new_version=""):
        self.old_version = old_version
        self.new_version = new_version


class XcdChkData:
    """
    This class is responsible for holding the data of the script.
    """

    # Disabled because dataclasses are not a thing in Python 3.6
    # pylint: disable=R0903

    def __init__(self):
        self.updated_pkgs: Dict[str, XcdChkUpdatedPackageVersion] = {}
        self.added_pkgs: Dict[str, str] = {}
        self.removed_pkgs: List[str] = []
        self.downgraded_pkgs = List[str]


class XcdCheckFetchOptions:
    """
    This class is responsible to hold the options for fetching data from xcdchk.
    """

    # Disabled because dataclasses are not a thing in Python 3.6
    # pylint: disable=R0903

    def __init__(self, url="", timeout=60):
        self.url = url
        self.timeout = timeout


class XcdCheckRawData:
    """
    This class is responsible for holding the raw data of the script.
    """

    # Disabled because dataclasses are not a thing in Python 3.6
    # pylint: disable=R0903

    def __init__(self):
        self.changelog = ""
        self.updated = ""
        self.new = ""
        self.missing = ""
        self.downgraded = ""


def xcdchk_fetch_data(
    version: str,
    origin_version: str,
    build1: str,
    build2: str,
    xcdchk_options: XcdCheckFetchOptions,
) -> XcdCheckRawData:
    """
    Fetches the data of xcdchk.

    :param version: The SLES version that is paired to the newer of the two builds.
    :param origin_version: The SLES version that is paired to the older version of the two builds.
    :param build1: The older of the two builds.
    :param build2: The newer of the two builds.
    :param xcdchk_options: The options that are used to fetch the data from xcdchk
    :return: The object that contains all the data that is needed for the script to work.
    """
    xcdchk_url = xcdchk_options.url
    xcdchk_timeout = xcdchk_options.timeout
    common_part = f"{origin_version}-Full-Test-Build{build1}-Build{build2}"
    result = XcdCheckRawData()
    result.changelog = requests.get(
        f"{xcdchk_url}/raw/{version}-Full-Test/{build2}/all/ChangeLog-{common_part}",
        timeout=xcdchk_timeout,
    ).text
    result.updated = requests.get(
        f"{xcdchk_url}/raw/{version}-Full-Test/{build2}/all/{common_part}-updated-RPMs",
        timeout=xcdchk_timeout,
    ).text
    result.new = requests.get(
        f"{xcdchk_url}/raw/{version}-Full-Test/{build2}/all/{common_part}-new-RPMs",
        timeout=xcdchk_timeout,
    ).text
    result.missing = requests.get(
        f"{xcdchk_url}/raw/{version}-Full-Test/{build2}/all/{common_part}-missing-RPMs",
        timeout=xcdchk_timeout,
    ).text
    result.downgraded = requests.get(
        f"{xcdchk_url}/raw/{version}-Full-Test/{build2}/all/{common_part}-downgraded-RPMs",
        timeout=xcdchk_timeout,
    ).text
    return result


def __get_package_names(changelog: str) -> Dict[str, List[str]]:
    add_update_regex = re.compile(
        r"^(?P<change>o Updated|o Added)\W(?P<package_name>.*)(\W\(.*\))",
        flags=re.MULTILINE,
    )
    result: Dict[str, List[str]] = {"updated": [], "added": []}
    for match in add_update_regex.finditer(changelog):
        if match.group("change") == "o Updated":
            result["updated"].append(match.group("package_name"))
        elif match.group("change") == "o Added":
            result["added"].append(match.group("package_name"))
    return result


def xcdchk_updated_pkgs(
    changelog: str, updated: str
) -> Dict[str, XcdChkUpdatedPackageVersion]:
    """
    This function parses the updated packages from their changelogs and then searches for the version from and to
    version in the updated packages file.

    :param changelog: The changelog to search through.
    :param updated: The updated packages to search through.
    :return: The keys are package names and the value of each key is the NamedTuple "XcdChkUpdatedPackageVersion".
    """
    result = {}
    package_names = __get_package_names(changelog)
    upgrade_regex = re.compile(
        r"(?P<name>.*)\.(?P<arch>.*):\s(?P<old_version>.*)\s=>\s(?P<new_version>.*)"
    )
    for package in package_names.get("updated", []):
        for line in updated.split("\n"):
            if line.startswith(package):
                match = upgrade_regex.match(line)
                if match is not None:
                    result[package] = XcdChkUpdatedPackageVersion(
                        match.group("old_version"), match.group("new_version")
                    )
    for package in package_names.get("added", []):
        for line in updated.split("\n"):
            if line.startswith(package):
                match = upgrade_regex.match(line)
                if match is not None:
                    result[package] = XcdChkUpdatedPackageVersion(
                        match.group("old_version"), match.group("new_version")
                    )
    return result


def xcdchk_added_pkgs(changelog: str, added: str) -> Dict[str, str]:
    """
    This function parses the added packages from their changelogs and then searches for the version from and to
    version in the added packages file.

    :param changelog: The changelog to search through.
    :param added: The added packages to search through.
    :return: A dict where package names are keys and versions are the values.
    """
    package_names = __get_package_names(changelog)
    result = {}
    package_version_regex = re.compile(
        r"(?P<name>.*)-(?P<version>[^-]*)-(?P<build>[^-]*)\..*"
    )
    for package in package_names.get("added", []):
        for line in added.split("\n"):
            if line.startswith(package):
                match = package_version_regex.match(line)
                if match is not None:
                    result[package] = match.group("version")
    for package in package_names.get("updated", []):
        for line in added.split("\n"):
            if line.startswith(package):
                result[package] = ""
    return result


def xcdchk_removed_pkgs(missing_rpms: str) -> List[str]:
    """
    This function parses the removed packages from the removed packages file.

    :param missing_rpms: The file to search through where missing RPMs are listed.
    :return: The list of packages has been removed.
    """
    package_name_regex = re.compile(r"(-[^-]*\..*)")
    packages: List[str] = []
    for line in missing_rpms.split("\n"):
        if "x86_64" in line or "noarch" in line:
            package_name_match = next(package_name_regex.finditer(line))
            if package_name_match is not None:
                packages.append(line[: package_name_match.start()])

    # Filter kernel and debug packages
    filter_regex = re.compile(r"^kernel|.*debugsource.*|.*debuginfo.*")
    result: List[str] = []
    for package in packages:
        filter_match = filter_regex.match(package)
        if filter_match is None:
            # Append if regex DOESN'T apply
            result.append(package)
    return result


def xcdchk_downgraded_pkgs(
    downgraded_rpms: str,
) -> Dict[str, XcdChkUpdatedPackageVersion]:
    """
    Parse the list of downgraded packages and return a well formatted result for further work.

    :param downgraded_rpms: The str with the list of downgraded packages.
    :returns: A dictionary where the keys are package names and the value for each package is a version object.
    """
    downgrade_regex = re.compile(
        r"(?P<name>.*)\.(?P<arch>.*):\s(?P<old_version>.*)\s=>\s(?P<new_version>.*)"
    )
    result: Dict[str, XcdChkUpdatedPackageVersion] = {}
    for match in downgrade_regex.finditer(downgraded_rpms):
        result[match.group("name")] = XcdChkUpdatedPackageVersion(
            match.group("old_version"), match.group("new_version")
        )
    return result


def xcdchk_mentioned_bugs(changelog: str) -> List[str]:
    """
    Find all openSUSE, SUSE or Novell Bugzilla references in the changelog.

    :param changelog: The str with the full changelog.
    :returns: The sorted list with the Bugzilla bug numbers.
    """
    regex_bugzilla = re.compile(r"(bsc#|bnc#|boo#)(\d{7})", flags=re.M)
    bugs_set: Set[str] = set()
    for match in regex_bugzilla.finditer(changelog):
        bugs_set.add(match.group(2))

    return sorted(bugs_set)


def build_bsc_query_p1_p2(changelog: str) -> str:
    """
    Builds the query for all P1 & P2 bugs that can be found in Bugzilla.

    :params changelog: The str with the full changelog.
    :returns: The str with the full URL that includes the query.
    """
    bugs_list = xcdchk_mentioned_bugs(changelog)
    bugs = "%2C".join(bugs_list)  # Seperated by %2C which is ","
    url = "https://bugzilla.suse.com/buglist.cgi?"
    return (
        f"{url}bug_id={bugs}"
        f"&bug_id_type=anyexact"
        f"&bug_status=RESOLVED"
        f"&bug_status=VERIFIED"
        f"&columnlist=short_desc"
        f"&priority=P1%20-%20Urgent"
        f"&priority=P2%20-%20High"
        f"&product=PUBLIC%20SUSE%20Linux%20Enterprise%20Desktop%2015%20SP5"
        f"&product=PUBLIC%20SUSE%20Linux%20Enterprise%20High%20Availability%20Extension%2015%20SP5"
        f"&product=PUBLIC%20SUSE%20Linux%20Enterprise%20HPC%2015%20SP5"
        f"&product=PUBLIC%20SUSE%20Linux%20Enterprise%20Server%2015%20SP5"
        f"&product=SUSE%20Linux%20Enterprise%20Desktop%2015%20SP5"
        f"&product=SUSE%20Linux%20Enterprise%20High%20Availability%20Extension%2015%20SP5"
        f"&product=SUSE%20Linux%20Enterprise%20HPC%2015%20SP5"
        f"&product=SUSE%20Linux%20Enterprise%20HPC%2015%20SP5%20in%20Public%20Clouds"
        f"&product=SUSE%20Linux%20Enterprise%20Server%2015%20SP5"
        f"&product=SUSE%20Linux%20Enterprise%20Server%2015%20SP5%20in%20Public%20Clouds"
        f"&product=SUSE%20Linux%20Enterprise%20Server%20for%20SAP%2015%20SP5%20in%20Public%20Clouds"
        f"&product=SUSE%20Linux%20Enterprise%20Server%20for%20SAP%20Applications%2015%20SP5"
        f"&query_based_on=SLE_15SP5_Resolved_issues"
        f"&query_format=advanced"
        f"&resolution=FIXED"
    )


def mentioned_jira_references(changelog: str) -> List[str]:
    """
    Scans a given changelog for SLE and PED issues.

    :param changelog: The str with the full changelog between two images.
    :returns: The list of SLE and PED issues that can be found.
    """
    jira_ped_regex = re.compile(r"jsc#SLE-[0-9]{5}|jsc#PED-[0-9]{1,5}")
    result: Set[str] = set()
    for match in jira_ped_regex.finditer(changelog):
        result.add(match.group())
    return sorted(result)


def build_ped_list(changelog: str) -> List[str]:
    """
    Scans a given changelog for PED issues.

    :param changelog: The str with the full changelog between two images.
    :returns: The list of PED issues that can be found.
    """
    result = set()
    ped_regex = re.compile(r"PED-[0-9]{1,5}")
    for match in ped_regex.finditer(changelog):
        result.add(match.group())
    return sorted(result)


JiraResponse = namedtuple("JiraResponse", "query comment labels")


def build_jira_query_incorrect(ped: str, build2: str) -> JiraResponse:
    """
    Builds a Jira Query that shows all issues that are in an incorrect state and that must be manually handled.

    :param ped: The list of ped issues seperated by commas.
    :param build2: The newer of the two build numbers available to the script.
    :returns: The built JiraResponse tuple.
    """
    allowed_stati = [
        "QE Open",
        "QE In Progress",
        "QE Blocked",
        "Engineering Done",
        "Dev In Progress",
        "IBS Integration",
    ]
    allowed_stati_str = '","'.join(allowed_stati)
    return build_jira_query(
        (
            f"issue in ({ped})"
            f' AND status NOT IN ("{allowed_stati_str}")'
            " AND type = Implementation"
        ),
        (
            f"A submit request referencing this feature has been merged into build{build2}.\n"
            "Please update the state of this ticket, as it doesn't reflect the correct state of development."
        ),
        "Add status:wait_for_status\nAdd status:code_merged",
    )


def build_jira_query_development(ped: str, build2: str) -> JiraResponse:
    """
    Builds a Jira Query that shows all issues that are in development state.

    :param ped: The list of ped issues seperated by commas.
    :param build2: The newer of the two build numbers available to the script.
    :returns: The built JiraResponse tuple.
    """
    return build_jira_query(
        f'issue in ({ped}) AND status = "Dev In Progress" AND type = Implementation',
        f"A submit request referencing this feature has been merged into build{build2}.",
        "Remove status:wait_for_status\nAdd status:code_merged",
    )


def build_jira_query_completed(ped: str, build2: str) -> JiraResponse:
    """
    Builds a Jira Query that shows all issues that are in a completed state.

    :param ped: The list of ped issues seperated by commas.
    :param build2: The newer of the two build numbers available to the script.
    :returns: The built JiraResponse tuple.
    """
    return build_jira_query(
        (
            f"issue in ({ped})"
            ' AND status IN ("QE Open","QE In Progress","QE Blocked","Engineering Done")'
            " AND type = Implementation"
        ),
        f"A submit request referencing this feature has been merged into build{build2}.",
        'no handling required, only remove stale "status:" labels',
    )


def build_jira_query_ready(ped: str, build2: str) -> JiraResponse:
    """
    Builds a Jira Query that shows all issues that are ready to be moved to their next status automatically.

    :param ped: The list of ped issues seperated by commas.
    :param build2: The newer of the two build numbers available to the script.
    :returns: The built JiraResponse tuple.
    """
    return build_jira_query(
        f'issue in ({ped}) AND status = "IBS Integration" AND type = Implementation',
        f"A submit request referencing this feature has been merged into build{build2}.",
        "Remove status:code_merged\nRemove status:wait_for_status",
    )


def build_jira_query(query: str, comment: str, labels: str) -> JiraResponse:
    """
    Builds a JIRA query tuple.

    :param query: The query that should be attached to the tuple.
    :param comment: The comment that should be attached to the tuple.
    :param labels: The labels that should be attached to the tuple.
    :returns: The built JiraResponse tuple.
    """
    return JiraResponse(query, comment, labels)


PackageUpdatedFromXcdChkResult = namedtuple(
    "PackageUpdatedFromXcdChkResult",
    "xcdchk_data bsc_query jira_references jira_queries",
)


def main(
    version: str,
    origin_version: str,
    build1: str,
    build2: str,
    xcdchk_options: XcdCheckFetchOptions,
) -> PackageUpdatedFromXcdChkResult:
    """
    Main routine executes the non-CLI related logic.
    """
    xcdchk_sources = xcdchk_fetch_data(
        version,
        origin_version,
        build1,
        build2,
        xcdchk_options,
    )
    xcdchk_data = {
        "updated": xcdchk_updated_pkgs(
            xcdchk_sources.changelog,
            xcdchk_sources.updated,
        ),
        "added": xcdchk_added_pkgs(
            xcdchk_sources.changelog,
            xcdchk_sources.new,
        ),
        "removed": xcdchk_removed_pkgs(xcdchk_sources.missing),
        "downgraded": xcdchk_downgraded_pkgs(xcdchk_sources.downgraded),
        "mentioned_bugs": xcdchk_mentioned_bugs(xcdchk_sources.changelog),
    }
    bsc_query = build_bsc_query_p1_p2(xcdchk_sources.changelog)
    jira_references = mentioned_jira_references(xcdchk_sources.changelog)
    ped_list = build_ped_list(xcdchk_sources.changelog)
    jira_queries = {
        "incorrect": build_jira_query_incorrect(",".join(ped_list), build2),
        "development": build_jira_query_development(",".join(ped_list), build2),
        "completed": build_jira_query_completed(",".join(ped_list), build2),
        "ready": build_jira_query_ready(",".join(ped_list), build2),
    }
    return PackageUpdatedFromXcdChkResult(
        xcdchk_data, bsc_query, jira_references, jira_queries
    )


def print_jira_query(header: str, jira_query: str, comment: str, labels: str):
    """
    Formats a JIRA query for printing to stdout.
    """
    print_template = f"""
{header}
=========================================
Query:
------
{jira_query}
Comment:
--------
{comment}
Labels:
-------
{labels}"""
    print(print_template)


def print_from_to_version_package(name: str, from_version: str, to_version: str):
    """
    Formats a package that has a version for printing on stdout.
    """
    print(f"* {name}: {from_version} => {to_version}")


def main_cli(args):
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    result = main(
        args.service_pack,
        args.origin_service_pack,
        args.builds[0],
        args.builds[1],
        XcdCheckFetchOptions(args.xcdchk_url, args.xcdchk_timeout),
    )

    print("Updated packages:")
    for package, version in result.xcdchk_data.get("updated").items():
        print_from_to_version_package(package, version.old_version, version.new_version)
    print("")
    print("Added packages:")
    for package, version in result.xcdchk_data.get("added").items():
        print(f"* {package} {version}")
    print("")
    print("Removed packages:")
    for package in result.xcdchk_data.get("removed"):
        print(f"* {package}")
    print("")
    print("Downgraded packages:")
    for package, version in result.xcdchk_data.get("downgraded").items():
        print_from_to_version_package(package, version.old_version, version.new_version)
    print("")
    print("Mentioned bug references:")
    print(",".join(result.xcdchk_data.get("mentioned_bugs")))
    print("")
    print(f"Filter for resolved P1/P2 bugs with this build in {args.service_pack}")
    print(result.bsc_query)
    print("")
    print("Mentioned JIRA references:")
    print(",".join(result.jira_references))
    print("")
    print_jira_query(
        "JIRA query for incorrect state",
        result.jira_queries.get("incorrect").query,
        result.jira_queries.get("incorrect").comment,
        result.jira_queries.get("incorrect").labels,
    )
    print_jira_query(
        "JIRA query for still under development",
        result.jira_queries.get("development").query,
        result.jira_queries.get("incorrect").comment,
        result.jira_queries.get("incorrect").labels,
    )
    print_jira_query(
        "JIRA query for already completed features",
        result.jira_queries.get("completed").query,
        result.jira_queries.get("incorrect").comment,
        result.jira_queries.get("incorrect").labels,
    )
    print_jira_query(
        "JIRA query for features ready to transition",
        result.jira_queries.get("ready").query,
        result.jira_queries.get("incorrect").comment,
        result.jira_queries.get("incorrect").labels,
    )
