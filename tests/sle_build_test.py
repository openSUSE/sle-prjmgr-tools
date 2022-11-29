import pytest

from sle_prjmgr_tools import sle_build


@pytest.fixture(scope="function", autouse=True)
def setup_osc():
    sle_build.osc_prepare("tests/data/oscrc", "https://api.suse.de")


def test_osc_get_builds():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-15-SP5:GA:TEST"

    # Act
    result = sle_build.osc_get_builds(apiurl, project)

    # Assert
    print(result)
    assert False


def test_sle_15_media_build():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-15-SP5:GA"
    # TODO: Mock osc_get_builds to achieve consistent results

    # Act
    result = sle_build.sle_15_media_build(apiurl, project)

    # Assert
    print(result)
    assert False


def test_osc_sle_non_release_packages():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-15-SP5:GA"

    # Act
    result = sle_build.osc_get_sle_non_release_packages(apiurl, project)

    # Assert
    print(result)
    assert False


def test_osc_get_build_flavors():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-15-SP5:GA"

    # Act
    result = sle_build.osc_get_build_flavors(apiurl, project, "kiwi-templates-Minimal", "_multibuild")

    # Assert
    assert result == ['kvm-and-xen', 'kvm', 'VMware', 'MS-HyperV', 'OpenStack-Cloud', 'RaspberryPi']


def test_osc_get_non_product_packages():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-15-SP5:GA"

    # Act
    result = sle_build.osc_get_non_product_packages(apiurl, project)

    # Assert
    print(result)
    assert False


def test_get_kiwi_template():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-15-SP5:GA"

    # Act
    result = sle_build.get_kiwi_template(apiurl, project)

    # Assert
    assert result == "kiwi-templates-Minimal"


def test_get_sle_images_jeos():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-15-SP5:GA"
    kiwi_template = "kiwi-templates-Minimal"

    # Act
    result = sle_build.get_sle_images_jeos(apiurl, project, kiwi_template)

    # Assert
    print(result)
    assert False


def test_get_sle_images_multibuild():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-15-SP5:GA"

    # Act
    result = sle_build.get_sle_images_multibuild(apiurl, project)

    # Assert
    print(result)
    assert False


def test_get_images_old_style():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-15-SP5:GA"

    # Act
    result = sle_build.get_sle_images_old_style(apiurl, project)

    # Assert
    print(result)
    assert False


def test_sle_images():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-15-SP5:GA"

    # Act
    result = sle_build.sle_images(apiurl, project)

    # Assert
    print(result)
    assert False


def test_osc_get_dvd_images():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "15-SP5"

    # Act
    result = sle_build.osc_get_dvd_images(apiurl, project)

    # Assert
    print(result)
    assert False


def test_get_wsl_binaries():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-15-SP5:Update:WSL:Update:CR"

    # Act
    result = sle_build.get_wsl_binaries(apiurl, project)

    # Assert
    print(result)
    assert False


def test_osc_get_sle_12_images():
    # Arrange
    apiurl = "https://api.suse.de"
    project = "SUSE:SLE-12-SP5:GA"

    # Act
    result = sle_build.osc_get_sle_12_images(apiurl, project)

    # Assert
    print(result)
    assert False


def test_main():
    # Arrange
    version = ""

    # Act
    result = sle_build.main(version)

    # Assert
    print(result)
    assert False
