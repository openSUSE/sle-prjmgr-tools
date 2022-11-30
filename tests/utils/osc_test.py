import pytest

from sle_prjmgr_tools.utils import osc


OSC_SERVER = "https://api.suse.de"
OVERRIDE_CONFIG = "tests/data/oscrc"


@pytest.fixture
def osc_utils():
    def _osc_utils_factory(osc_server: str):
        return osc.OscUtils(osc_server=osc_server, override_config=OVERRIDE_CONFIG)

    return _osc_utils_factory


@pytest.fixture
def osc_release_helper():
    def _osc_release_helper_factory(osc_server: str):
        return osc.OscReleaseHelper(
            osc_server=osc_server, override_config="tests/data/oscrc"
        )

    return _osc_release_helper_factory


def test_object_creation():
    # Arrange
    # Act
    result = osc.OscUtils(
        osc_server="https://api.suse.de", override_config=OVERRIDE_CONFIG
    )

    # Assert
    assert isinstance(result, osc.OscUtils)


def test_osc_get_binary_names(osc_utils):
    # Arrange
    osc_utils_obj = osc_utils(OSC_SERVER)
    project = "SUSE:SLE-15-SP5:GA"

    # Act
    result = osc_utils_obj.osc_get_binary_names(
        project, "standard", "x86_64", "000release-packages:SLES-release"
    )

    # Assert
    print(result)
    assert False


def test_osc_get_textfile_from_rpm(osc_utils):
    # Arrange
    osc_utils_obj = osc_utils(OSC_SERVER)
    project = "SUSE:SLE-15-SP5:GA"

    # Act
    result = osc_utils_obj.osc_get_textfile_from_rpm(
        project, "standard", "x86_64", "sles-release", "etc/products.d/SLES.prod"
    )

    # Assert
    print(result)
    assert False


def test_osc_retrieve_betaversion(osc_utils):
    # Arrange
    osc_utils_obj = osc_utils(OSC_SERVER)
    project = "SUSE:SLE-15-SP5:GA"

    # Act
    result = osc_utils_obj.osc_retrieve_betaversion(project)

    # Assert
    assert result == "Snapshot-202211-1"


def test_osc_is_repo_published(osc_utils):
    # Arrange
    osc_utils_obj = osc_utils(OSC_SERVER)
    project = "SUSE:SLE-15-SP5:GA"
    repository = "images"

    # Act
    result = osc_utils_obj.osc_is_repo_published(project, repository)

    # Assert
    assert result


def test_osc_get_containers(osc_utils):
    # Arrange
    osc_utils_obj = osc_utils(OSC_SERVER)
    project = "SUSE:SLE-15-SP5:GA"
    expected_result = [
        "cdi-apiserver-container",
        "cdi-cloner-container",
        "cdi-controller-container",
        "cdi-importer-container",
        "cdi-operator-container",
        "cdi-uploadproxy-container",
        "cdi-uploadserver-container",
        "virt-api-container",
        "virt-controller-container",
        "virt-exportproxy-container",
        "virt-exportserver-container",
        "virt-handler-container",
        "virt-launcher-container",
        "virt-libguestfs-tools-container",
        "virt-operator-container",
    ]

    # Act
    result = osc_utils_obj.osc_get_containers(project)

    # Assert
    assert result == expected_result


def test_osc_get_products(osc_utils):
    # Arrange
    osc_utils_obj = osc_utils(OSC_SERVER)
    project = "SUSE:SLE-15-SP5:GA"
    expected_result = [
        "SLES15-SP5",
        "SLES15-SP5-BYOS",
        "SLES15-SP5-CHOST-BYOS",
        "SLES15-SP5-EC2-ECS-HVM",
        "SLES15-SP5-HPC",
        "SLES15-SP5-HPC-BYOS",
        "SLES15-SP5-Hardened-BYOS",
        "SLES15-SP5-SAP",
        "SLES15-SP5-SAP-Azure-LI-BYOS",
        "SLES15-SP5-SAP-Azure-VLI-BYOS",
        "SLES15-SP5-SAP-BYOS",
        "SLES15-SP5-SAPCAL",
    ]

    # Act
    result = osc_utils_obj.osc_get_products(project)

    # Assert
    assert result == expected_result


@pytest.mark.skip
def test_osc_do_release(osc_utils):
    # Arrange
    osc_utils_obj = osc_utils(OSC_SERVER)
    project = "SUSE:SLE15-SP5:GA"

    # Act
    osc_utils_obj.osc_do_release(project)

    # Assert
    assert False


def test_osc_get_jsc_from_sr(osc_utils):
    # Arrange
    osc_utils_obj = osc_utils(OSC_SERVER)
    sr_number = 284017
    expected_result = [
        "PED-1183",
        "PED-1504",
        "PED-1509",
        "PED-1517",
        "PED-1559",
        "PED-1817",
        "PED-1917",
        "PED-1981",
        "PED-2064",
        "PED-606",
        "PED-818",
        "PED-850",
    ]

    # Act
    result = osc_utils_obj.osc_get_jsc_from_sr(sr_number)

    # Assert
    assert result == expected_result


# ---------------- Release Helper ----------------


@pytest.mark.skip
def test_release_to_common(osc_release_helper):
    # Arrange
    osc_release_helper_obj = osc_release_helper(OSC_SERVER)
    project = "SUSE:SLE15-SP5:GA"

    # Act
    osc_release_helper_obj.release_to_common(project)

    # Assert
    assert False


@pytest.mark.skip
def test_release_repo_to_test(osc_release_helper):
    # Arrange
    osc_release_helper_obj = osc_release_helper(OSC_SERVER)
    project = "SUSE:SLE15-SP5:GA"

    # Act
    osc_release_helper_obj.release_repo_to_test(project)

    # Assert
    assert False


@pytest.mark.skip
def test_release_repo_to_publish(osc_release_helper):
    # Arrange
    osc_release_helper_obj = osc_release_helper(OSC_SERVER)
    project = "SUSE:SLE15-SP5:GA"

    # Act
    osc_release_helper_obj.release_repo_to_publish(project)

    # Assert
    assert False
