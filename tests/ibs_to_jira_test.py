import argparse

import pytest

from sle_prjmgr_tools import ibs_to_jira
from sle_prjmgr_tools.utils.jira import SSLOptions


@pytest.fixture(scope="module")
def jira_work_obj(request) -> ibs_to_jira.JiraWork:
    pat_token = request.config.getoption("--pat-token")
    ssl_options = SSLOptions(
        True, "/usr/share/pki/trust/anchors/SUSE_Trust_Root.crt.pem"
    )
    return ibs_to_jira.JiraWork(
        "https://jira-devel.suse.de",
        pat_token,
        ssl_options,
    )


def test_build_parser():
    # Arrange
    parser = argparse.ArgumentParser(prog="main parser")
    subparsers = parser.add_subparsers(help="subparser")
    program_input = ["ibs_to_jira", "-j", "my_pat"]

    # Act
    ibs_to_jira.build_parser(subparsers)
    result = parser.parse_args(program_input)

    # Assert
    assert result.jira_pat == "my_pat"


def test_osc_collect_srs_between_builds():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-15-SP5:GA"
    duration = 100

    # Act
    result = ibs_to_jira.osc_collect_srs_between_builds(apiurl, project, duration)

    # Assert
    assert False


def test_transform_srs_per_jsc_to_jsc_per_sr():
    # Arrange
    input_data = {1234: ["abc", "def"], 5678: ["ghi", "jkl"]}
    expected_result = {
        "abc": [1234],
        "def": [1234],
        "ghi": [5678],
        "jkl": [5678],
    }

    # Act
    result = ibs_to_jira.transform_srs_per_jsc_to_jsc_per_sr(input_data)

    # Assert
    assert result == expected_result


def test_jira_search_correct(jira_work_obj):
    # Arrange
    jsc = ["PED-141"]

    # Act
    result = jira_work_obj.jira_search_correct(jsc)

    # Assert
    assert result == jsc


def test_jira_post_comment_correct(jira_work_obj):
    # Arrange

    # Act & Assert
    # No Exception is enough that this test passes
    jira_work_obj.jira_post_comment_correct("PED-141", [1234, 5678])


def test_jira_search_incorrect(jira_work_obj):
    # Arrange
    jsc = ["PED-158"]

    # Act
    result = jira_work_obj.jira_search_incorrect(jsc)

    # Assert
    assert result == jsc


def test_jira_post_comment_incorrect(jira_work_obj):
    # Arrange
    issue = "PED-123"
    srs = [123, 124]

    # Act
    jira_work_obj.jira_post_comment_incorrect(issue, srs)

    # Assert
    assert False


def test_jira_search_development(jira_work_obj):
    # Arrange
    jscs = ["PED-157"]

    # Act
    results = jira_work_obj.jira_search_development(jscs)

    # Assert
    assert results == jscs


def test_jira_post_comment_development(jira_work_obj):
    # Arrange
    issue = "PED-123"
    srs = [123, 124]

    # Act
    jira_work_obj.jira_post_comment_development(issue, srs)

    # Assert
    assert False


def test_jira_search_other(jira_work_obj):
    # Arrange
    # Act
    jira_work_obj.jira_search_other()

    # Assert
    assert False


def test_jira_post_comment_other(jira_work_obj):
    # Arrange
    issues = "PED-123"
    srs = [123, 124, 125]

    # Act
    jira_work_obj.jira_post_comment_other(issues, srs)

    # Assert
    assert False


@pytest.mark.skip("Test not fully set up for testing!")
def test_main(request):
    # Arrange
    pat_token = request.config.getoption("--pat-token")

    # Act
    ibs_to_jira.main(pat_token)

    # Assert
    assert False
