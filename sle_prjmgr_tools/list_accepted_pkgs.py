"""
Module to list all accepted SRs that are accepted that changed, added or removed a package.
"""
import time
from typing import Optional, Tuple

from osc import conf, core  # type: ignore


def build_parser(parent_parser):
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.

    :return: The subparsers object from argparse.
    """
    subparser = parent_parser.add_parser(
        "list_accepted_pkgs", help="list_accepted_pkgs help"
    )
    subparser.add_argument("--project", "-p", dest="project", type=str, required=True)
    subparser.add_argument("--days", "-d", dest="time_range", type=int)
    subparser.set_defaults(func=main_cli)


def osc_prepare(osc_config: Optional[str] = None, osc_server: Optional[str] = None):
    """
    This has to be executed to the ini-style config is converted into their corresponding types.

    :param osc_config: Path to the configuration file for osc. The default delegates the task to the osc library.
    :param osc_server: Server URL that points to the OBS server API.
    """
    conf.get_config(override_conffile=osc_config, override_apiurl=osc_server)


def osc_get_submit_requests(project: str):
    """
    Looks in the IBS the list of requests up that are accepted and submitted.

    :param project: The project that should be checked.
    :return: The list of requests objects that are found with the state accepted and that are submitted.
    """
    return core.get_review_list(
        "https://api.suse.de", project=project, states=("accepted"), req_type="submit"
    )


def osc_get_delete_requests(project: str):
    """
    Looks in the IBS the list of requests up that are accepted and that delete a package.

    :param project: The project that should be checked.
    :return: The list of requests objects that are found with the state accepted and that are deleting a package.
    """
    return core.get_review_list(
        "https://api.suse.de", project=project, states=("accepted"), req_type="delete"
    )


def filter_requests(days: int, requests) -> list:
    """
    Filter a given list by its date. The time of days is respected and not rounded. A request that was submitted at
    2pm on the earliest days that is included would be ignored if it is 3pm during execution of this method.

    :param days: The days that should be filtered
    :param requests: The list with the requests to filter.
    :return: Filter list where every request is younger than the days specified.
    """
    result = []
    earliest_date = time.strftime(
        "%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - days * 24 * 3600)
    )
    for request in requests:
        if request.state.when > earliest_date:
            result.append(request)
    return result


def main_cli(args):
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    # Parse arguments
    submit_requests, delete_requests = main(
        args.osc_instance, args.project, args.time_range
    )
    # Print both retrieved lists with format: "pkg-name (YYYY-MM-DDThh:mm:ss) hyperlink-to-request"
    print("==============================")
    print("SUBMIT REQUESTS")
    print("==============================")
    for request in submit_requests:
        print(
            f"{request.actions[0].src_package} ({request.state.when}) https://api.suse.de/{request.reqid}"
        )
    print("==============================")
    print("DELETE REQUESTS")
    print("==============================")
    for request in delete_requests:
        print(
            f"{request.actions[0].src_package} ({request.state.when}) https://api.suse.de/{request.reqid}"
        )


def main(apiurl: str, project: str, time_range: int) -> Tuple[list, list]:
    """
    Main routine executes the non-CLI related logic.

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project that should be queried.
    :param time_range: The list of days that present the delimiter for the filter
    :return: A Tuple with the list of requests
    """
    # Prepare osc -> Config is ini style and needs to be converted first
    osc_prepare(osc_server=apiurl)
    # Retrieve SRs
    submit_requests = osc_get_submit_requests(project)
    # Retrieve SRs with delete requests
    delete_requests = osc_get_delete_requests(project)
    # Filter requests by days
    submit_requests = filter_requests(time_range, submit_requests)
    delete_requests = filter_requests(time_range, delete_requests)
    return submit_requests, delete_requests
