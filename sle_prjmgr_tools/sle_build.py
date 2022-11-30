"""
This module is responsible to collect the current build numbers of the various images that are built.
"""
import concurrent.futures
import re
from typing import Dict, List, Optional
from urllib.error import HTTPError

from lxml import etree
from osc import conf, core  # type: ignore


class Build:
    """
    Helper class that holds data about a single build.
    """

    # Disabled because dataclasses are not a thing in Python 3.6
    # pylint: disable=R0903

    def __init__(self, name="", mtime=0):
        self.name = name
        self.mtime = mtime
        self.kind = ""
        self.number = ""


class SleBuildData:
    """
    Helper class that holds all the builds and image names in one object.
    """

    # Disabled because dataclasses are not a thing in Python 3.6
    # pylint: disable=R0903

    def __init__(self):
        self.codestream = ""
        self.builds_ga: Dict[str, Build] = {}
        self.builds_test: Dict[str, Build] = {}
        self.builds_publish: Dict[str, Build] = {}
        self.images_test = []
        self.images_publish = []
        self.images_wsl = []


def build_parser(parent_parser):
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.

    :param parent_parser: The subparsers object from argparse.
    """
    subparser = parent_parser.add_parser("sle_build", help="sle_build help")
    subparser.add_argument("version", metavar="V", help="project to get the builds for")
    subparser.set_defaults(func=main_cli)


def osc_prepare(osc_config: Optional[str] = None, osc_server: Optional[str] = None):
    """
    This has to be executed to the ini-style config is converted into their corresponding types.

    :param osc_config: Path to the configuration file for osc. The default delegates the task to the osc library.
    :param osc_server: Server URL that points to the OBS server API.
    """
    conf.get_config(override_conffile=osc_config, override_apiurl=osc_server)


def osc_get_builds(apiurl: str, project: str) -> List[Build]:
    """
    Get builds from the build-service.

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    :return: The list with the image names.
    """
    result = []
    query = {
        "package": "000product",
        "multibuild": "1",
        "repository": "images",
        "arch": "local",
        "view": "binarylist",
    }
    url = core.makeurl(apiurl, ["build", project, "_result"], query=query)
    file_object_builds = core.http_GET(url)
    tree = etree.parse(file_object_builds)
    binary_list = tree.xpath("//resultlist/result/binarylist/binary[@filename]")
    regex_iso_filename = re.compile(
        r".*(DVD|cd-cd|Packages|Full|Online)-x86_64.*Media1.iso$"
    )
    for binary in binary_list:
        filename_attribute = binary.get("filename")
        mtime_attribute = binary.get("mtime")
        if regex_iso_filename.match(filename_attribute):
            result.append(Build(filename_attribute, mtime_attribute))
    return result


def sle_15_media_build(apiurl: str, project: str) -> Dict[str, Build]:
    """
    Searches in the specified project for the current build flavors with their corresponding id.

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    :return: A dict where the keys are the build flavor and the values the build number.
    """
    result = {}
    regex_output = re.compile(
        r"(.*DVD|.*cd-cd|.*Packages|.*Full|.*Online)-x86_64-(Build.*)-Media1.iso"
    )
    for build in osc_get_builds(apiurl, project):
        build_number_match = regex_output.match(build.name)
        if build_number_match is None:
            raise ValueError("No regex match for build number!")
        build.kind = build_number_match.group(1)
        build.number = build_number_match.group(2)
        result[build.kind] = build
    return result


def osc_get_sle_non_release_packages(apiurl: str, project: str):
    """
    Retrieve all packages that are not related to a release.

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    :return: The list of packages.
    """
    package_list = core.meta_get_packagelist(apiurl, project)
    result = []
    for package in package_list:
        if package.startswith("SLE") and "release" not in package:
            result.append(package)
    return result


def osc_get_build_flavors(
    apiurl: str, project: str, package: str, filename: str
) -> list:
    """
    Reads the sources of a package to retrieve the allowed build flavors of an image.

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    :param package: The package where the multibuild file is located is.
    :param filename: The name of the multibuild file.
    :return: The list of flavors.
    """
    url = core.makeurl(apiurl, ["source", project, package, filename])
    try:
        file_object_osc_cat = core.http_GET(url)
    except HTTPError as error:
        if error.code == 404:
            # Package has no multibuild file
            return []
        raise
    root = etree.parse(file_object_osc_cat)
    elements = root.xpath("//multibuild/flavor")
    result = []
    for element in elements:
        result.append(element.text)
    return result


def osc_get_non_product_packages(apiurl: str, project: str) -> List[str]:
    """
    Get a list of packages that are unrelated to the product building progress.

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    :return: The list of packages.
    """
    package_list = core.meta_get_packagelist(apiurl, project)
    result = []
    package_list.remove("000product")
    for package in package_list:
        if "_product" in package or "kiwi" in package:
            continue
        result.append(package)
    return result


def get_kiwi_template(apiurl: str, project: str) -> str:
    """
    Retrieve the name of the kiwi template package

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    :return: The full name of the kiwi-template package.
    """
    project_packages = core.meta_get_packagelist(apiurl, project)
    kiwi_template = ""
    for package in project_packages:
        if package.startswith("kiwi-templates"):
            kiwi_template = package
            break
    return kiwi_template


def get_sle_image_jeos_single(
    apiurl: str, project: str, repo, kiwi_template: str, i
) -> List[str]:
    """
    Search for JeOS images in a given project, repo and with the specified kiwi template.

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    :param repo: The repository to search for jeos images.
    :param kiwi_template: The full name of the kiwi package.
    :param i: The flavor of the package that is being searched for.
    :return: The images that have been found.
    """
    result = []
    binaries = core.get_binarylist(
        apiurl, project, repo.name, repo.arch, f"{kiwi_template}:{i}"
    )
    for binary in binaries:
        if binary.endswith(".packages"):
            result.append(binary[:-9])
    return result


def get_sle_images_jeos(apiurl: str, project: str, kiwi_template: str) -> List[str]:
    """
    multibuild JeOS

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    :param kiwi_template: The full name of the kiwi package.
    :return: The list of names that the images from JeOS/Minimal will have.
    """
    result = []
    # core.get_repos_of_project returns an iterator
    repos = list(core.get_repos_of_project(apiurl, project))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in osc_get_build_flavors(apiurl, project, kiwi_template, "_multibuild"):
            for repo in repos:
                futures.append(
                    executor.submit(
                        get_sle_image_jeos_single,
                        apiurl,
                        project,
                        repo,
                        kiwi_template,
                        i,
                    )
                )
        for future in concurrent.futures.as_completed(futures):
            result.extend(future.result())
    return result


def get_sle_images_multibuild_single(
    apiurl: str, project: str, repo, package: str, flavor: str
):
    """
    Retrieve a list of images.

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    :param repo: The repository to get the images from.
    :param package: The package where the images are in.
    :param flavor: The flavor of the package that should be checked.
    :return: The list of images.
    """
    result = []
    binaries = core.get_binarylist(
        apiurl, project, repo.name, repo.arch, f"{package}:{flavor}"
    )
    for binary in binaries:
        if binary.endswith(".packages"):
            result.append(binary[:-9])
    return result


def get_sle_images_multibuild(apiurl: str, project: str):
    """
    Multibuild images such as cloud etc., typical name is "SLE12-SP5-EC2". This is for 15.2+ and 12.5+.

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    """
    result = []
    # core.get_repos_of_project returns an iterator
    repos = list(core.get_repos_of_project(apiurl, project))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for package in osc_get_sle_non_release_packages(apiurl, project):
            for flavor in osc_get_build_flavors(
                apiurl, project, package, "_multibuild"
            ):
                for repo in repos:
                    futures.append(
                        executor.submit(
                            get_sle_images_multibuild_single,
                            apiurl,
                            project,
                            repo,
                            package,
                            flavor,
                        )
                    )
        for future in concurrent.futures.as_completed(futures):
            result.extend(future.result())
    return result


def get_sle_images_old_style_single(apiurl: str, project, repo, i):
    """
    Retrieve the old style image names.

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    :param repo: The repository to search for images.
    :param i: The package to search for old-style images.
    :return: The names of the images as a list.
    """
    result = []
    binaries = core.get_binarylist(apiurl, project, repo.name, repo.arch, i)
    for binary in binaries:
        if binary.endswith(".packages"):
            result.append(binary[:-9])
    return result


def get_sle_images_old_style(apiurl: str, project: str):
    """
    old style

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    """
    result = []
    # core.get_repos_of_project returns an iterator
    repos = []
    for repo in list(core.get_repos_of_project(apiurl, project)):
        if repo.name == "images":
            repos.append(repo)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in osc_get_non_product_packages(apiurl, project):
            for repo in repos:
                futures.append(
                    executor.submit(
                        get_sle_images_old_style_single, apiurl, project, repo, i
                    )
                )
        for future in concurrent.futures.as_completed(futures):
            result.extend(future.result())
    return result


def sle_images(apiurl: str, project: str) -> List[str]:
    """
    Collects all SLE 15 style images that can be found and sorts them.

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look at.
    :return: The list of images that can be found.
    """
    temp_storage = []
    kiwi_template = get_kiwi_template(apiurl, project)
    if kiwi_template != "":
        jeos_images = get_sle_images_jeos(apiurl, project, kiwi_template)
        temp_storage.extend(jeos_images)

    multibuild_images = get_sle_images_multibuild(apiurl, project)
    temp_storage.extend(multibuild_images)
    old_style_images = get_sle_images_old_style(apiurl, project)
    temp_storage.extend(old_style_images)

    temp_storage.sort()
    return temp_storage


def osc_get_dvd_images(apiurl: str, version: str) -> List[str]:
    """
    Get all SLE 12 style DVD images.

    :param apiurl: URL where the API from the build-service can be reached.
    :param version: The version of SLE to look for.
    :return: The list of images that can be found.
    """
    packages = core.meta_get_packagelist(apiurl, f"SUSE:SLE-{version}:GA")
    result = []
    product_regex = re.compile(r"_product.*(DVD-x86|cd-cd.*x86_64)")
    for package in packages:
        if product_regex.match(package):
            result.append(package)
    return result


def get_wsl_binaries(apiurl: str, project: str) -> List[str]:
    """
    This method avoids displaying images-test/$arch.

    :param apiurl: URL where the API from the build-service can be reached.
    :param project: The project to look for WSL images in.
    :return: A list of names for build WSL images.
    """
    result = []
    try:
        binary_list = core.get_binarylist(
            apiurl,
            project,
            "standard",
            "x86_64",
            "wsl-appx",
        )
    except HTTPError as http_error:
        if http_error.code != 404:
            # All non 404 should be raised loudly
            raise
        # Something do not exist, thus no binary available
        binary_list = []

    for binary in binary_list:
        if binary.endswith(".appx"):
            result.append(binary)
    return result


def osc_get_sle_12_images(apiurl: str, version: str) -> Dict[str, Build]:
    """
    Retrieves the list of SLE 12 images.

    :param apiurl: URL where the API from the build-service can be reached.
    :param version: The version of SLE to check for.
    :return: A dict where the keys are build flavors and the values are build ids.
    """
    result = {}
    for image in osc_get_dvd_images(apiurl, version):
        my_media = core.get_binarylist(
            "https://api.suse.de/",
            f"SUSE:SLE-{version}:GA",
            "images",
            "local",
            package=image,
        )
        builds = []
        for media in my_media:
            if (
                media.endswith("Media1.iso") or media.endswith("Media.iso")
            ) and "x86_64" in media:
                builds.append(media)
        regex_build = re.compile(r"(.*)-DVD.*x86_64-(Build[0-9]+)-Media(1)?\.iso")
        if len(builds) == 1:
            my_match = regex_build.match(builds[0])
            if my_match is None:
                raise ValueError("No match for the regex of the build number!")
            build = Build(name=builds[0])
            build.kind = my_match.group(1)
            build.number = my_match.group(2)
            result[build.kind] = build
    return result


def main(apiurl: str, version: str, osc_config: Optional[str] = None) -> SleBuildData:
    """
    Main function to get the builds for the specified version.

    :param apiurl: URL where the API from the build-service can be reached.
    :param version: The version of the product to check. Should be in format "<codestream>-SP<number>"
    :param osc_config: The config location for osc to use. If None then the default is retrieved by osc.
    :return: Object with the summarized data.
    """
    # Preparations
    result = SleBuildData()
    result.codestream = version.split("-", 1)[0]

    # Prepare osc
    osc_prepare(osc_config=osc_config, osc_server=apiurl)

    # Special cases
    if result.codestream == "15":
        result.builds_ga = sle_15_media_build(apiurl, f"SUSE:SLE-{version}:GA")
        result.builds_test = sle_15_media_build(apiurl, f"SUSE:SLE-{version}:GA:TEST")
        result.builds_publish = sle_15_media_build(
            apiurl, f"SUSE:SLE-{version}:GA:PUBLISH"
        )
    else:
        result.builds_ga = osc_get_sle_12_images(apiurl, version)

    result.images_test = sle_images(apiurl, f"SUSE:SLE-{version}:GA:TEST")
    result.images_publish = sle_images(apiurl, f"SUSE:SLE-{version}:GA:PUBLISH")
    result.images_wsl = get_wsl_binaries(
        apiurl, f"SUSE:SLE-{version}:Update:WSL:Update:CR"
    )

    return result


def main_cli(args):
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    data = main(args.osc_instance, args.version, osc_config=args.osc_config)
    if data.codestream == "15":
        print(f"builds from SUSE:SLE-{args.version}:GA:")
        for build, version in data.builds_ga.items():
            print(f"{build}:\t\t{version.number}")
        print("")

        print(f"builds from SUSE:SLE-{args.version}:GA:TEST:")
        for build, version in data.builds_test.items():
            print(f"{build}:\t\t{version.number}")
        print("")

        print(f"builds from SUSE:SLE-{args.version}:GA:PUBLISH")
        for build, version in data.builds_publish.items():
            print(f"{build}:\t\t{version.number}")
    else:
        print(f"builds from SUSE:SLE-{args.version}:GA:")
        for build, version in data.builds_ga.items():
            print(f"{build}:\t\t{version.number}")

    # Normal process
    print("")
    print(f"images from SUSE:SLE-{args.version}:GA:TEST:")
    for image in data.images_test:
        print(image)

    print("")
    print(f"images from SUSE:SLE-{args.version}:GA:PUBLISH:")
    for image in data.images_publish:
        print(image)

    # avoid displaying images-test/$arch
    print("")
    print(f"WSL image (from SUSE:SLE-{args.version}:Update:WSL:Update:CR):")
    if len(data.images_wsl) > 0:
        for binary in data.images_wsl:
            print(binary)
    else:
        print("No binary available or package not found!")
