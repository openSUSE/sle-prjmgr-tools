"""
This module should contain helper functionality that assists for Jira.
"""
import logging
from collections import namedtuple
from typing import Dict, List, Union

import jira

SSLOptions = namedtuple("SSLOptions", "check_cert truststore")


class JiraUtils:
    """
    This class contains the shared functions that will enable scripts to interact with JIRA.
    """

    def __init__(self, jira_url: str, pat_token: str, ssl_options: SSLOptions):
        """
        Default constructor that initializes the object.

        Authentication is only possible doing PAT. For more information follow up on the Atlassian Documentation:

            https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html

        :param jira_url: URL to access the JIRA instance.
        :param pat_token: The token to access the JIRA instance. Will define if a script can access the required
                          resources.
        :param ssl_options: The NamedTuple that contains the options to configure the SSL setup.
        """
        self.logger = logging.getLogger()
        self.jira_url = jira_url
        options = self.__prepare_ssl_options(ssl_options)
        self.jira_obj = jira.JIRA(
            self.jira_url,
            options=options,
            token_auth=pat_token,
        )

    @staticmethod
    def __prepare_ssl_options(ssl_options: SSLOptions) -> dict:
        """
        Prepares the SSL options dict for the JIRA Client.

        :param ssl_options: The NamedTuple that contains the options to configure the SSL setup.
        :return: The dictionary that will be passed to the JIRA library and in the end to requests.
        """
        result: Dict[str, Union[str, bool]] = {}
        if ssl_options.check_cert:
            result["verify"] = ssl_options.truststore
        else:
            result["verify"] = False
        return result

    def jira_get_field_values(self, field_id: str, issue: str) -> Dict[str, str]:
        """
        Retrieves a list of all available field values in a select or multi-select.

        :param field_id: The ID of the field that the values should be retrieved for.
        :param issue: The issue that decides the field values that are available to search for.
        :return: The dict of possible field values or an empty dict. Keys represent the names and values are the IDs.
        """
        result = {}
        issue_obj = self.jira_obj.issue(issue)
        meta = self.jira_obj.editmeta(issue_obj.key)
        for option in meta["fields"][field_id]["allowedValues"]:
            result[option.get("value")] = option.get("id")
        return result

    def jira_get_field_name(self, name: str) -> str:
        """
        Retrieve the field ID by the name of the field that an end user sees.

        :param name: The name of the field.
        :return: The field ID or an emtpy string.
        """
        result = ""
        jira_fields = self.jira_obj.fields()
        for field in jira_fields:
            if field.get("name") == name:
                field_id = field.get("id")
                if isinstance(field_id, str):
                    result = field_id
                    break
                # Should never happen since the ID is always
                # a str but mypy requires this logic.
                continue
        return result

    def jira_get_version_obj(self, issue: str, name: str):
        """
        Get the version object that represents a version in JIRA:

        :param issue: The issue that decides the versions that are available to search for.
        :param name: The name of the version that should be retrieved
        :return: The full version object as returned by the JIRA library.
        """
        issue_obj = self.jira_obj.issue(issue)
        project = issue_obj.get_field("project")
        for version in self.jira_obj.project_versions(project):
            if version.name == name:
                return version
        return None

    def jira_get_transition_id(self, jsc: str, transition_name: str) -> str:
        """
        Retrieve the transition ID of a ticket by the transition name.

        :param jsc: The Jira ticket number.
        :param transition_name: Name of the transition.
        :return: The target transition ID or an empty str.
        """
        transitions = self.jira_obj.transitions(jsc)
        target_transition_id = ""
        for transition in transitions:
            if transition.get("name") == transition_name:
                target_transition_id = transition.get("id")
        return target_transition_id

    def jira_transition_tickets(self, jsc: str) -> None:
        """
        Transition an issue in the workflow if it is in the correct state. If not log a message.

        :param jsc: The Jira ticket number.
        """
        target_transition_id = self.jira_get_transition_id(jsc, "Integrated")
        if target_transition_id == "":
            self.logger.error(
                'Issue "%s" could not be transitioned to the state "QE Open" because the transition could not be'
                " identified!",
                jsc,
            )
            return
        self.jira_obj.transition_issue(jsc, target_transition_id)

    def jira_do_search(self, jql: str, max_results: int = 50) -> List[str]:
        """
        Perform a JIRA search.

        JQL documentation: https://confluence.atlassian.com/jiracoreserver073/advanced-searching-861257209.html

        :param jql: The JQL that should be used for searching.
        :param max_results: The number of results that should be
        :return: The list of issue keys that match the filter. The number of results is limited by ``max_results``.
        """
        result: List[str] = []
        for issue in self.jira_obj.search_issues(jql, maxResults=max_results):
            if isinstance(jira.Issue, str):
                result.append(issue.key)
        return result
