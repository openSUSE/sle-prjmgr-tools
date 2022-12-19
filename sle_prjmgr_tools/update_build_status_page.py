"""
Updates the build status page on Confluence for the service pack that is given with information from IBS.
"""

import getpass
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from typing import Any, Dict, Set, Union

import requests

JIRA_PASSWORD_FILE = os.path.expanduser("~/.jira_susedotcom_password")
NEXT_BUILD_DAYS = 7
PROJECT_TO_PAGE_MAP = {
    "test": {
        "page_id": 243269754,
        "url": "https://confluence.suse.com/display/SUSELinuxEnterpriseServer12SP5/Test",
    },
    "SUSE:SLE-12-SP5:GA": {
        "page_id": 227442811,
        "url": "https://confluence.suse.com/display/SUSELinuxEnterpriseServer12SP5/Build+status+SLE+12+SP5",
    },
    "SUSE:SLE-15-SP1:GA": {
        "page_id": 203129002,
        "url": "https://confluence.suse.com/display/SUSELinuxEnterpriseServer15SP1/Build+status",
    },
    "SUSE:SLE-15-SP2:GA": {
        "page_id": 255262891,
        "url": "https://confluence.suse.com/display/SUSELinuxEnterpriseServer15SP2/Build+Status",
    },
    "SUSE:SLE-15-SP3:GA": {
        "page_id": 415957115,
        "url": "https://confluence.suse.com/display/SUSELinuxEnterpriseServer15SP3/Build+Status",
    },
    "SUSE:SLE-15-SP4:GA": {
        "page_id": 798884391,
        "url": "https://confluence.suse.com/display/SUSELinuxEnterpriseServer15SP4/Build+Status",
    },
    "SUSE:SLE-15-SP5:GA": {
        "page_id": 1058603270,
        "url": "https://confluence.suse.com/display/SUSELinuxEnterpriseServer15SP5/Build+Status",
    },
}
NEXT_BUILD_DATE = None

page_cache: Dict[
    str, Any
] = {}  # to limit amount of rest calls {page_id: expanded_body.json}


def build_parser(parent_parser):
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.

    :param parent_parser: The subparsers object from argparse.
    """
    global NEXT_BUILD_DATE  # pylint: disable=W0603
    NEXT_BUILD_DATE = datetime.now() + timedelta(days=NEXT_BUILD_DAYS)

    subparser = parent_parser.add_parser(
        "update_build_status_page", help="update_build_status_page help"
    )
    subparser.add_argument(
        "project",
        metavar="PROJECT",
        help="SUSE:PROJECT:GA",
        nargs=1,
        choices=PROJECT_TO_PAGE_MAP.keys(),
    )
    product_group = subparser.add_argument_group("Confluence Server related options")
    product_group.add_argument(
        "--next-build-date",
        help=f"YYYY-mm-dd Adjusts a date of next build. Default is in {date.strftime(NEXT_BUILD_DATE, '%Y-%m-%d')}",
        default=date.strftime(NEXT_BUILD_DATE, "%Y-%m-%d"),
    )
    product_group.add_argument(
        "--build-id",
        help="Build id is autodetected from output of sle_common/sle-build. But you can override it.",
    )
    product_group.add_argument(
        "--build-label",
        help="Will append label behind build id. E.g. Alpha-1.0-candidate",
    )
    server_group = subparser.add_argument_group("Confluence Server related options")
    server_group.add_argument(
        "--server",
        help="JIRA Server (devel by default), could be also url",
        default="https://confluence.suse.com/rest/api",
    )

    server_group.add_argument(
        "--user", help=f"JIRA user [{os.getenv('USER')}]", default=os.getenv("USER")
    )
    server_group.add_argument("--auth", help="JIRA authentication", default="basic")
    server_group.add_argument(
        "--password",
        help=f"JIRA/Confluence password. Can be also stored in {JIRA_PASSWORD_FILE}",
    )
    subparser.set_defaults(func=main_cli)


def get_project(project: str):
    """
    Retrieves the desired project.

    :param project: The project to work with.
    :return: The project or SLES 15 SP1 for testing.
    """
    if project == "test":
        return "SUSE:SLE-15-SP1:GA"
    return project


def free_page_cache(url: str):
    """
    Checks if a page is cached and removes it if it is.

    :param url: The URL to check.
    """
    for addr in list(page_cache.keys()):
        if addr == "url" or addr.startswith(f"{url}?"):
            del page_cache[addr]


def confluence_generate_build_summary(
    server: str,
    user: str,
    password: str,
    project: str,
    build_id: int,
    build_label: str,
    changelog: str,
):
    """
    Merge manually pre-filled section for next build with changelog from the build

    :param server: Confluence server URL
    :param user: The user for Confluence to log in with.
    :param password: The password for Confluence to log in with.
    :param project: The project in the IBS to work with.
    :param build_id: The override ID of the build that is being worked with.
    :param build_label: The override label of the build that is being worked with.
    :param changelog: The cached output of the ``sle_build`` script.
    :return: The generated build summary.
    """
    # pylint: disable=R0913
    build_str = str(build_id)
    if build_label:
        build_str = f"{build_id} - {build_label}"

    pre_filled = confluence_get_next_build_section(
        server, user, password, page_id_by_project(project)
    )
    summary = pre_filled.replace(
        '<ac:parameter ac:name="title">Next build</ac:parameter>',
        f'<ac:parameter ac:name="title">Build {build_str} ({datetime.now().strftime("%Y%m%d")})</ac:parameter>',
    )
    # replace only the last </p> or </ul> with </p> or </ul> followed by <p>ourlist</p>
    summary = re.sub(
        r"(</[a-z]*>)\s*</ac:rich-text-body>",
        rf"\1<p><br /><br />{to_html_list(changelog)}</p></ac:rich-text-body>",
        summary,
    )
    match = re.search(r'<time datetime="(?P<date>\d+-\d+-\d+)" />', summary)
    if match:
        summary = re.sub(
            r'<time datetime="\d+-\d+-\d+" />',
            f'<time datetime="{datetime.now().strftime("%Y-%m-%d")}" />',
            summary,
        )
    return summary


def confluence_get_prev_builds(server: str, user: str, password: str, project: str):
    """
    Retrieve the old page content of the specified project.

    :param server: Confluence server URL
    :param user: The user for Confluence to log in with.
    :param password: The password for Confluence to log in with.
    :param project: The IBS project to work with.
    :return: The page content of the Confluence page for the specified IBS project.
    """
    content = confluence_get_page_content(
        server, user, password, page_id_by_project(project), expand=True
    )
    # print (content)
    content = content["body"]["storage"]["value"]
    next_build_section = confluence_get_next_build_section(
        server, user, password, page_id_by_project(project)
    )
    next_bs_start = content.find(next_build_section)
    return content[next_bs_start + len(next_build_section) :]


def to_html_list(data: str):
    """
    Converts a newline seperated str into a HTML tag seperated str.

    :param data: The str to convert.
    :return: The str with newlines replaced by the HTML ``<br />`` tag.
    """
    result = ""
    for line in data.split("\n"):
        if line.strip():
            result += f"{line}<br />"
    return result


def get_last_build_number(project, changelog=None):
    """
    Retrieves the last build ID from the ``sle_build`` script.

    :param project: The project name in IBS.
    :param changelog: The changelog from the build.
    :return: The build number.
    """
    # I'm getting build id as the highest number from the changelog
    # sle12 and sle15 both have different syntax
    versions: Set[Union[int, float]] = set()
    if not changelog:
        changelog = get_last_build_changelog(
            project
        )  # reuse if possible, it takes a lot of time

    project = get_project(project)

    if project.startswith("SUSE:SLE-12"):
        # SLE-12-SP5-HPC:		Build0151
        for line in changelog.split("\n"):
            version = re.search("([0-9]+)$", line)
            if version:
                versions.add(int(version.groups()[0]))
    elif project.startswith("SUSE:SLE-15"):
        # SLE-15-SP1-Installer:		Build224.10
        for line in changelog.split("\n"):
            version = re.search(r"([0-9]+\.[0-9]+)$", line)
            if version:
                versions.add(float(version.groups()[0]))
    # print versions
    return str(sorted(versions)[-1])  # sorted


def get_last_build_changelog(project: str):
    """
    Retrieves the output of the ``sle_build`` script.

    :param project: The project name in IBS.
    :return: The output of the ``sle_build`` script.
    """
    # Build id is ignored
    project = get_project(project)

    prj_match = re.search(r"SLE-(\d+-\w+):\w+", project)
    if prj_match is None:
        raise ValueError("Could not get project name from given project!")
    prj = prj_match.groups(0)[0]
    cmd = f"{os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sle-build')} {prj}"
    out = subprocess.check_output(cmd, shell=True)
    # Python3 returns bytes-like obj
    if not isinstance(out, str):
        return out.decode("utf-8")
    return out


def page_id_by_project(project: str):
    """
    Retrieve the page ID in Confluence by the IBS project name.

    :param project: The project name in IBS.
    :return: The page ID in Confluence.
    """
    return PROJECT_TO_PAGE_MAP[project]["page_id"]


def page_url_by_project(project: str):
    """
    Retrieve the page URL in Confluence by the IBS project name.

    :param project: The project name in IBS.
    :return: The URL to Confluence.
    """
    return PROJECT_TO_PAGE_MAP[project]["url"]


def confluence_get_next_build_section(
    server: str, user: str, password: str, page_id: int
):
    """
    Retrieve a section of a specified Confluence page.

    :param server: Confluence server URL
    :param user: The user for Confluence to log in with.
    :param password: The password for Confluence to log in with.
    :param page_id: The ID of the Confluence page.
    :return: The content of the desired page.
    """
    content = confluence_get_page_content(server, user, password, page_id, expand=True)
    # print content
    content = content["body"]["storage"]["value"]
    next_build_section = content[
        content.find("<ac:structured-macro") : content.find("</ac:structured-macro>")
        + len("</ac:structured-macro>")
    ]
    return next_build_section


def generate_new_build_section(next_build_date: date):
    """
    Generates a section for the next build that will be released.

    :param next_build_date: The date that will be used for the next build.
    :return: The Confluence formatted section for the next build.
    """
    next_build = f"""
    <ac:structured-macro ac:name="expand" ac:schema-version="1" ac:macro-id="6541c1a0-8ae5-4076-975c-7eb3c22fc21e">
      <ac:parameter ac:name="title">Next build</ac:parameter>
      <ac:rich-text-body>
        <p><time datetime="{date.strftime(next_build_date, "%Y-%m-%d")}" />
        &nbsp;</p><p>&nbsp;-----------------------------------------------------------------</p>
      </ac:rich-text-body>
    </ac:structured-macro>"""
    return next_build.replace("\n", "")


def confluence_get_page_content(
    server: str, user: str, password: str, page_id: int, expand=False
):
    """
    Retrieves the page content of a Confluence page.

    :param server: Confluence server URL
    :param user: The user for Confluence to log in with.
    :param password: The password for Confluence to log in with.
    :param page_id: The ID of the Confluence page.
    :param expand: Whether the page should be expanded or not.
    :return: The page content.
    """
    url = f"{server}/content/{page_id:d}"
    if expand:
        url += "?expand=body.storage"

    if url not in page_cache:
        auth = (user, password)
        confluence_request = requests.get(url, auth=auth, timeout=180)
        # print (url)
        if confluence_request.status_code == 401:
            raise ValueError("Authentication fail")
        page_cache[url] = confluence_request.json()
    return page_cache[url]


def confluence_get_page_heading(server: str, user: str, password: str, project: str):
    """
    Retrieves the heading of a Confluence page.

    :param server: Confluence server URL
    :param user: The user for Confluence to log in with.
    :param password: The password for Confluence to log in with.
    :param project: The project in the IBS to work with.
    :return: The heading of the confluence page for the IBS project.
    """
    content = confluence_get_page_content(
        server, user, password, page_id_by_project(project), expand=True
    )
    # print(content)
    content = content["body"]["storage"]["value"]
    next_build_section = confluence_get_next_build_section(
        server, user, password, page_id_by_project(project)
    )
    next_bs_start = content.find(next_build_section)
    return content[:next_bs_start]


def confluence_set_page_content(
    server: str, user: str, password: str, page_id: int, json_content
):
    """
    Update a Confluence page with the given content.

    :param server: Confluence server URL
    :param user: The user for Confluence to log in with.
    :param password: The password for Confluence to log in with.
    :param page_id: The page ID to update.
    :param json_content: The JSON content that the Confluence API should expect.
    """
    current_data = confluence_get_page_content(server, user, password, page_id)
    new_data = {
        "id": page_id,
        "type": current_data["type"],
        "space": {"key": current_data["space"]["key"]},
        "title": current_data["title"],
        "version": {"number": int(current_data["version"]["number"]) + 1},
    }
    new_data.setdefault("body", {}).setdefault(
        "storage", {"representation": "storage"}
    )["value"] = json_content
    # print(json.dumps(new_data, indent=4, sort_keys=True))

    url = f"{server}/content/{page_id:d}"
    free_page_cache(url)

    confluence_request = requests.put(
        url,
        data=json.dumps(new_data),
        auth=(user, password),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=180,
    )

    try:
        confluence_request.raise_for_status()
    except requests.HTTPError as http_error:
        print(http_error.response.text)
        raise http_error


def confluence_update_build_summary(
    server: str,
    user: str,
    password: str,
    project: str,
    build_id: int,
    changelog,
    next_build_date: date,
    build_label,
):
    """
    Updates the build summary of a Confluence page for a certain IBS project.

    :param server: Confluence server URL
    :param user: The user for Confluence to log in with.
    :param password: The password for Confluence to log in with.
    :param project: The project in the IBS to work with.
    :param build_id: The override ID of the build that is being worked with.
    :param changelog: The cached output of the ``sle_build`` script.
    :param next_build_date: Date of the next build.
    :param build_label: The override label of the build that is being worked with.
    """
    # pylint: disable=R0913
    new_page_body = confluence_get_page_heading(server, user, password, project)
    new_page_body += generate_new_build_section(next_build_date)
    new_page_body += confluence_generate_build_summary(
        server, user, password, project, build_id, build_label, changelog
    )

    new_page_body += confluence_get_prev_builds(server, user, password, project)
    confluence_set_page_content(
        server, user, password, page_id_by_project(project), new_page_body
    )


def main(
    server: str,
    user: str,
    password: str,
    build_id,
    build_label,
    next_build_date: str,
    project: str,
):
    """
    Main routine executes the non-CLI related logic.

    :param server: Confluence server URL
    :param user: The user for Confluence to log in with.
    :param password: The password for Confluence to log in with.
    :param build_id: The override ID of the build that is being worked with.
    :param build_label: The override label of the build that is being worked with.
    :param next_build_date: The date of the next build.
    :param project: The project in the IBS to work with.
    """
    # pylint: disable=R0913
    if not password:

        if os.path.exists(JIRA_PASSWORD_FILE):
            try:
                with open(JIRA_PASSWORD_FILE, encoding="UTF-8") as fp_password_file:
                    user, password = fp_password_file.read().strip().split("\n")
            except ValueError:
                print(
                    f"Error: {JIRA_PASSWORD_FILE} is supposed to contain exactly two lines user and password."
                )
                sys.exit(1)

        else:
            print(
                f"You can save confluence/jira user and password into {JIRA_PASSWORD_FILE} (two separate lines). To"
                "avoid re-entering"
            )
            password = getpass.getpass(
                f"Please enter {server} password for user {user}: "
            )

    changelog = get_last_build_changelog(project)
    if not build_id:
        build_id = get_last_build_number(project, changelog=changelog)

    confluence_update_build_summary(
        server,
        user,
        password,
        project,
        build_id,
        changelog,
        datetime.strptime(next_build_date, "%Y-%m-%d"),
        build_label,
    )

    print(f"Updated {page_url_by_project(project)}")


def main_cli(args):
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    main(
        args.server,
        args.user,
        args.password,
        args.build_id,
        args.build_label,
        args.next_build_date,
        args.project[0],
    )
