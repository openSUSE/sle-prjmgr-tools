"""
Script to post comments to Jira once an SR is included in a build and - if in state "IBS integration" transitions the
ticket to the next state.
"""
import enum
import logging
from typing import Dict, List, Optional

from sle_prjmgr_tools import list_accepted_pkgs, sle_build
from sle_prjmgr_tools.utils.jira import JiraUtils, SSLOptions
from sle_prjmgr_tools.utils.osc import OscUtils, OscReleaseHelper


class IssueState(enum.Enum):
    """
    Enum that contains all issue states that should be grouped for comments.
    """

    CORRECT = 1
    INCORRECT = 2
    DEVELOPMENT = 3
    OTHER = 999


logger = logging.getLogger()


class JiraWork(JiraUtils):
    """
    This is a subclass that performs all the work that is required to be done in JIRA.
    """

    def __init__(
        self,
        jira_url: str,
        pat_token: str,
        ssl_options: SSLOptions,
        milestone_name: str = "",
    ):
        self.milestone_name = milestone_name
        super().__init__(jira_url, pat_token, ssl_options)

    def _build_comment_template(
        self,
        comment_template: str,
        srs: List[int],
        osc_api_url: str = "https://build.opensuse.org",
        build_number: str = "",
    ) -> str:
        """
        This is rendering the comment template for a JIRA comment.

        :param comment_template: The template with three placeholders. The first one will be the build_number, the
                                 second one the milestone text (" (<name>)") and the third one will be the list of SRs
                                 in an unordered JIRA list.
        :param srs: The list of OBS Submit Requests
        :param build_number: The build number
        :return: The rendered template
        """
        milestone_text = ""
        if self.milestone_name:
            milestone_text = f" ({self.milestone_name})"
        return comment_template % (
            build_number,
            milestone_text,
            format_list_of_srs(srs, osc_api_url),
        )

    def jira_search_correct(self, jscs: List[str]) -> List[str]:
        """
        This method searches for issue that are in the state that the workflow states as correct.

        :param jscs: The list of JIRA tickets that should be filtered.
        :return: The list of JIRA tickets that are matched by the filter.
        """
        issue_status_allowed = [
            "IBS Integration",
        ]
        issue_status_allowed_str = '","'.join(issue_status_allowed)
        correct_state = (
            f'issue in ({",".join(jscs)})'
            f' AND status = "{issue_status_allowed_str}"'
            f" AND type = Implementation"
        )
        return self.jira_do_search(correct_state, len(jscs))

    def jira_post_comment_correct(self, issue: str, srs: List[int]) -> None:
        """
        This posts a comment for issues that are deemed correct in the workflow.

        :param issue: The issue that a comment should be posted to.
        :param srs: The list of Submit Requests from the OBS that should be put into the comment.
        """
        comment_template = """
        A submit request referencing this feature has been merged into %s%s.
    
        Submit Requests:
        %s
        """
        comment = self._build_comment_template(
            comment_template,
            srs,
            "https://api.suse.de",
            "",
        )
        self.jira_obj.add_comment(issue, comment)
        issue_obj = self.jira_obj.issue(issue)
        if "status:code_merged" not in issue_obj.fields.labels:
            issue_obj.fields.labels.append("status:code_merged")
        if "status:wait_for_status" not in issue_obj.fields.labels:
            issue_obj.fields.labels.append("status:wait_for_status")
        issue_obj.update(fields={"labels": issue_obj.fields.labels})

    def jira_search_incorrect(self, jscs: List[str]) -> List[str]:
        """
        This method searches for issue that are in the state that the workflow states as incorrect.

        :param jscs: The list of JIRA tickets that should be filtered.
        :return: The list of issues that are found to be incorrect.
        """
        issue_status_disallowed = [
            "QE Open",
            "QE In Progress",
            "QE Blocked",
            "Engineering Done",
            "In Maintenance",
            "Dev In Progress",
            "IBS Integration",
        ]
        issue_status_disallowed_str = '","'.join(issue_status_disallowed)
        incorrect_state = (
            f'issue in ({",".join(jscs)}) '
            f'AND status NOT IN ("{issue_status_disallowed_str}") '
            "AND type = Implementation"
        )
        return self.jira_do_search(incorrect_state, len(jscs))

    def jira_post_comment_incorrect(self, issue: str, srs: List[int]) -> None:
        """
        This posts a comment for issues that are deemed incorrect in the workflow.

        :param issue: The issue that a comment should be posted to.
        :param srs: The list of SRs from the OBS that are related to this issue.
        """
        comment_template = """
        A submit request referencing this feature has been merged into %s%s.

        Please update the state of this ticket, as it doesn't reflect to correct state of development.

        Submit Requests:
        %s
        """
        comment = self._build_comment_template(
            comment_template, srs, "https://api.suse.de", ""
        )
        self.jira_obj.add_comment(issue, comment)
        issue_obj = self.jira_obj.issue(issue)
        if "status:wait_for_status" not in issue_obj.fields.labels:
            issue_obj.fields.labels.append("status:wait_for_status")
        if "status:code_merged" not in issue_obj.fields.labels:
            issue_obj.fields.labels.append("status:code_merged")
        issue_obj.update(fields={"labels": issue_obj.fields.labels})

    def jira_search_development(self, jscs: List[str]) -> List[str]:
        """
        This method searches for issue that are in the state that the workflow states as in development.

        :param jscs: The list of JIRA tickets that should be filtered.
        :return: The list of issues that are found to be in development.
        """
        development_state = f'issue in ({",".join(jscs)}) AND status = "Dev In Progress" AND type = Implementation'
        return self.jira_do_search(development_state, len(jscs))

    def jira_post_comment_development(self, issue: str, srs: List[int]) -> None:
        """
        This posts a comment for issues that are deemed in development in the workflow.

        :param issue: The issue that a comment should be posted to.
        :param srs: The list of SRs from the OBS that are related to this issue.
        """
        comment_template = """
        A submit request referencing this feature has been merged into %s%s.

        Submit Requests:
        %s
        """
        comment = self._build_comment_template(
            comment_template,
            srs,
            "https://api.suse.de",
            "",
        )
        self.jira_obj.add_comment(issue, comment)
        issue_obj = self.jira_obj.issue(issue)
        if "status:code_merged" not in issue_obj.fields.labels:
            issue_obj.fields.labels.append("status:code_merged")
        if "status:wait_for_status" not in issue_obj.fields.labels:
            issue_obj.fields.labels.remove("status:wait_for_status")
        issue_obj.update(fields={"labels": issue_obj.fields.labels})

    @staticmethod
    def jira_search_other(
        issues_by_category: Dict[IssueState, List[str]], list_with_jscs: List[str]
    ) -> List[str]:
        """
        This method searches for issues that are in the state that the workflow states as not defined.

        :param issues_by_category: This is the dict with the pre-filtered issues by category.
        :param list_with_jscs: The list of JIRA tickets that should be filtered.
        :return: The list of issues that are remaining.
        """
        result: List[str] = list_with_jscs.copy()
        for jsc in list_with_jscs:
            for jsc_list in issues_by_category.values():
                if jsc in jsc_list:
                    result.remove(jsc)
        return result

    def jira_post_comment_other(self, issue: str, srs: List[int]) -> None:
        """
        This posts a comment to an issue that cannot be classified by one of the filters that are defined.

        :param issue: The issue that a comment should be posted to.
        :param srs: The list of SRs from the OBS that are related to this issue.
        """
        comment_template = """
        A submit request referencing this feature has been merged into %s%s.

        Submit Requests:
        %s
        """
        comment = self._build_comment_template(
            comment_template, srs, "https://api.suse.de", ""
        )
        self.jira_obj.add_comment(issue, comment)


def build_parser(parent_parser) -> None:
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.

    :param parent_parser: The subparsers object from argparse.
    """
    subparser = parent_parser.add_parser("ibs_to_jira", help="ibs_to_jira help")
    subparser.add_argument(
        "--jira-pat",
        "-j",
        required=True,
        dest="jira_pat",
        help='JIRA PAT token that can be created under "Profile" > "Personal Access Tokens" > "Create token".',
    )
    subparser.add_argument(
        "--ssl-cert-bundle",
        "-s",
        dest="ssl_cert_bundle",
        help="Path to the CA bundle that will be used by the script to verify the SSL certificates of Jira.",
        default="/usr/share/pki/trust/anchors/SUSE_Trust_Root.crt.pem",
    )
    subparser.add_argument(
        "--ssl-cert-check-disable",
        "-S",
        dest="ssl_cert_check_disable",
        help="If this flag is set, then all SSL verification of Jira is disabled.",
        action="store_true",
    )
    subparser.add_argument(
        "--project",
        "-p",
        dest="project",
        help="Project to work with.",
        default="SUSE:SLE-15-SP5:GA",
    )
    subparser.add_argument(
        "--milestone",
        "-m",
        dest="milestone",
        help="If this flag is given the name of the milestone is put into the comment in Jira.",
        action="store_true",
    )
    subparser.set_defaults(func=main_cli)


def osc_collect_srs_between_builds(
    obs_url: str, project: str, duration: int
) -> List[int]:
    """
    Collects all SRS between the two builds that we have atm.

    :param obs_url: URL where the API from the build-service can be reached.
    :param project: The project to check for.
    :param duration: The duration that should be checked for. Is relative from execution time of script.
    :return: The number of SRs that were done in the timeframe.
    """
    result = []
    pkg_requests = list_accepted_pkgs.main(obs_url, project, duration)
    for request_type in pkg_requests:
        result.extend(request_type)
    return result


def transform_srs_per_jsc_to_jsc_per_sr(
    srs_with_jscs: Dict[int, List[str]]
) -> Dict[str, List[int]]:
    """
    Transform the list of submit requests with the corresponding JSC mentions to a list of JSC tickets with their
    corresponding SRs.

    :param srs_with_jscs: The initial data.
    :return: The dict with the submit requests grouped by jsc.
    """
    result: Dict[str, List[int]] = {}
    for submit_request, jscs in srs_with_jscs.items():
        for jsc in jscs:
            if jsc not in result:
                result[jsc] = []
            result[jsc].append(submit_request)
    return result


def format_list_of_srs(srs: List[int], web_ui_url: str) -> str:
    """
    Formats the list of SRs that are to be posted into the comment.

    :param srs: The list of Submit Requests from the OBS that should be put into the comment.
    :param web_ui_url: The URL that should be used to link a Submit Request to the Web UI.
    :return: The list in JIRA comment markup that will result in an unordered list.
    """
    srs_formatted_str = ""
    for submit_request in srs:
        srs_formatted_str += (
            f"- [{submit_request}|{web_ui_url}/request/show/{submit_request}]\n"
        )
    return srs_formatted_str


def main_osc_work(obs_url: str, osc_config: Optional[str], project: str) -> dict:
    """
    This encapsulates all the work that is done on the OBS side.

    :param obs_url: URL where the API from the build-service can be reached.
    :param osc_config: The path to the osc configuration. If not present this will be searched for by osc.
    :param project: The project that should be released.
    :return: The dictionary with the SRs as keys and the list of jscs as a values
    """
    osc_work = OscReleaseHelper(osc_server=obs_url, override_config=osc_config)

    # Check TEST (get build number and mtime)
    old_build = sle_build.sle_15_media_build(obs_url, project)
    # Do release
    osc_work.release_repo_to_test(project)
    # Check TEST (get build number and mtime)
    new_build = sle_build.sle_15_media_build(obs_url, project)

    duration = int(next(iter(old_build.values())).mtime) - int(
        next(iter(new_build.values())).mtime
    )

    if duration == 0:
        print("WARNING: BuildIDs are identical!")
    elif duration < 0:
        print("WARNING: GA has an older build den GA:TEST!")

    # Collect all SRs between the build numbers
    list_with_srs = osc_collect_srs_between_builds(obs_url, project, duration)
    # Collect all JSCs from the SRs
    dict_with_srs = {}
    for submit_request in list_with_srs:
        dict_with_srs[submit_request] = osc_work.osc_get_jsc_from_sr(submit_request)
    return dict_with_srs


# pylint: disable-next=too-many-arguments
def main_jira_work(
    jira_pat: str,
    jira_url: str,
    dict_with_jscs: Dict[str, List[int]],
    ssl_cert_bundle: str = "/usr/share/pki/trust/anchors/SUSE_Trust_Root.crt.pem",
    ssl_cert_check_disable: bool = False,
    milestone_name: str = "",
) -> None:
    """
    This subroutine is grouping together all work that is related to JIRA.

    :param jira_pat: The PAT for the JIRA instance.
    :param jira_url: The URL to the JIRA instance.
    :param dict_with_jscs: Dictionary that contains all jscs with their corresponding SRs from the OBS.
    :param ssl_cert_bundle: The path to the CA certificate bundle. If this is None, the fallback to certifi is used.
    :param ssl_cert_check_disable: If this is set to True one can skip certificate validation.
    :param milestone_name: The name of the milestone. Leave this empty to skip adding the milestone name to the
                           comment.
    """
    jira_work = JiraWork(
        jira_url,
        jira_pat,
        SSLOptions(ssl_cert_check_disable, ssl_cert_bundle),
        milestone_name,
    )

    # Setup dict & search
    issues_by_category = {
        IssueState.CORRECT: jira_work.jira_search_correct(list(dict_with_jscs.keys())),
        IssueState.INCORRECT: jira_work.jira_search_incorrect(
            list(dict_with_jscs.keys())
        ),
        IssueState.DEVELOPMENT: jira_work.jira_search_development(
            list(dict_with_jscs.keys())
        ),
    }
    issues_by_category[IssueState.OTHER] = jira_work.jira_search_other(
        issues_by_category, list(dict_with_jscs.keys())
    )

    # Duplicate detection
    issues_by_category_sum = 0
    for value in issues_by_category.values():
        issues_by_category_sum += len(value)
    if issues_by_category_sum != len(dict_with_jscs.keys()):
        logger.warning(
            "There were issues found that were not existing in JIRA or the current user has no access to!"
        )

    print(issues_by_category)
    # Post comments to Jira
    for category, issues in issues_by_category.items():
        for issue in issues:
            if category == IssueState.CORRECT:
                jira_work.jira_post_comment_correct(issue, dict_with_jscs[issue])
                jira_work.jira_transition_tickets(issue)
            elif category == IssueState.INCORRECT:
                jira_work.jira_post_comment_incorrect(issue, dict_with_jscs[issue])
            elif category == IssueState.DEVELOPMENT:
                jira_work.jira_post_comment_development(issue, dict_with_jscs[issue])
            elif category == IssueState.OTHER:
                jira_work.jira_post_comment_other(issue, dict_with_jscs[issue])


def main(
    jira_pat_token: str,
    obs_url: str = "https://api.suse.de",
    jira_url: str = "https://jira.suse.de",
    obs_project: str = "SUSE:SLE-15-SP5:GA",
    osc_config: Optional[str] = None,
    ssl_cert_bundle: str = "/usr/share/pki/trust/anchors/SUSE_Trust_Root.crt.pem",
    ssl_cert_check_disable: bool = False,
    is_milestone: bool = False,
) -> None:
    """
    Main routine that executes the script

    :param jira_pat_token: The token to authenticate against JIRA.
    :param obs_url: URL where the API from the build-service can be reached.
    :param jira_url: The URL to the JIRA instance.
    :param osc_config: The path to the osc configuration. If not present this will be searched for by osc.
    :param obs_project: The project that should be released.
    :param ssl_cert_bundle: The path to the CA certificate bundle. If this is None, the fallback to certifi is used.
    :param ssl_cert_check_disable: If this is set to True one can skip certificate validation.
    :param is_milestone: Whether this is a milestone or not. If it is, the name of it will be included.
    """
    # pylint: disable=R0913
    # OSC work
    dict_with_srs = main_osc_work(obs_url, osc_config, obs_project)
    print(dict_with_srs)
    # Calculate all SRs for every JSC
    dict_with_jscs = transform_srs_per_jsc_to_jsc_per_sr(dict_with_srs)
    milestone_name = ""
    if is_milestone:
        osc_work = OscUtils(obs_url)
        milestone_name = osc_work.osc_retrieve_betaversion(obs_project)
    # Jira work
    main_jira_work(
        jira_pat_token,
        jira_url,
        dict_with_jscs,
        ssl_cert_bundle,
        ssl_cert_check_disable,
        milestone_name,
    )


def main_cli(args) -> None:
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    main(
        args.jira_pat,
        args.osc_instance,
        args.jira_instance,
        args.project,
        args.osc_config,
        args.ssl_cert_bundle,
        args.ssl_cert_check_disable,
        args.milestone,
    )
    print("Script done")
