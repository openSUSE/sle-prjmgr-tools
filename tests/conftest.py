"""
Helper module that is shared by all tests and read by pytest.

More information:

    https://docs.pytest.org/en/6.2.x/fixture.html#scope-sharing-fixtures-across-classes-modules-packages-or-session
"""
import pytest

from sle_prjmgr_tools.utils.jira import JiraUtils, SSLOptions


def pytest_addoption(parser):
    parser.addoption(
        "--pat-token",
        required=True,
        action="store",
        help="This is the pat token that will be used during testing.",
    )


@pytest.fixture(scope="module")
def jira_obj(request):
    pat_token = request.config.getoption("--pat-token")
    ssl_options = SSLOptions(
        True, "/usr/share/pki/trust/anchors/SUSE_Trust_Root.crt.pem"
    )
    return JiraUtils(
        "https://jira-devel.suse.de",
        pat_token,
        ssl_options,
    )
