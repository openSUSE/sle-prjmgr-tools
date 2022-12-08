"""
This module should contain helper functionality that assists for the Open Build Service.
"""
import re
import sys
import time
from typing import List, Optional

from lxml import etree
from osc import conf, core  # type: ignore


class OscUtils:
    """
    This class contains the shared functions that will enable scripts to interact with an Open Build Service instance.
    """

    def __init__(
        self,
        osc_server: str = "https://build.opensuse.org",
        override_config: Optional[str] = None,
    ):
        """
        Default constructor that initializes the object.

        :param osc_server: Server URL that points to the OBS server API.
        :param override_config: Path to the configuration file for osc. The default delegates the task to the
                                osc library.
        """
        self.osc_server = osc_server
        self.osc_web_ui_url = ""
        self.override_config = override_config
        self.osc_prepare()

    def osc_prepare(self) -> None:
        """
        This has to be executed to the ini-style config is converted into their corresponding types.
        """
        conf.get_config(
            override_conffile=self.override_config, override_apiurl=self.osc_server
        )

    @staticmethod
    def convert_project_to_product(project: str) -> str:
        """
        Assumes the following schema: RootProject:SomeSubProject:MoreProjects:SLE-<digits>-SP<digits>:SomeProject

        :param project: Project to convert
        :return: A str in the form "SLES<major>-SP<SP version>".
        """
        project_parts = project.split(":")
        product_version = project_parts[-2].split("-")
        result = f"SLES{product_version[1]}-{product_version[2]}"
        return result

    def get_file_from_package(
        self,
        project: str,
        package: str,
        revision,
        filename: str,
        target_filename: Optional[str] = None,
    ):  # pylint: disable=R0913
        """
        Retrieve a given file from a package that is text based.

        :param project: The project the package is in.
        :param package: The package the file is in.
        :param revision: The file revision that should be downloaded.
        :param filename: The filename that should be downloaded.
        :param target_filename: If this is given, then the file will be downloaded with the specified name.
        """
        core.get_source_file(
            self.osc_server,
            project,
            package,
            filename,
            targetfilename=target_filename,
            revision=revision,
        )

    def osc_get_web_ui_url(self) -> str:
        """
        Search the API for the Web UI URL.

        :return: The URL of the WebUI for OBS.
        """
        if self.osc_web_ui_url != "":
            return self.osc_web_ui_url
        obs_config_xml = core.show_configuration(self.osc_server)
        root = etree.fromstring(obs_config_xml)
        node = root.find("obs_url")
        if node is None or not node.text:
            raise ValueError("obs_url configuration element expected")
        self.osc_web_ui_url = node.text
        return self.osc_web_ui_url

    def osc_is_repo_published(self, project: str, repository: str) -> bool:
        """
        Checks if the repository in the specified project is already published. This does not reflect if the current
        build is published just that the build available via the API is published.

        :param project: The project that should be checked.
        :param repository: The repository that should be checked.
        :return: True if the repository is published.
        """
        url = core.makeurl(
            self.osc_server,
            ["build", project, "_result"],
            query={"view": "summary", "repository": repository},
        )
        with core.http_GET(url) as result:
            my_str = result.read().decode()
        root = etree.fromstring(my_str)
        my_nodes = root.xpath(f'/resultlist/result[@project="{project}"]')
        return all(
            (
                node.get("code") == "published" and node.get("state") == "published"
                for node in my_nodes
            )
        )

    def osc_get_containers(self, project: str) -> List[str]:
        """
        Searches in a given project for the packages that correspond to containers.

        :param project: The project that should be searched in.
        :return: The list of str with package names that match the container regex.
        """
        package_list = core.meta_get_packagelist(self.osc_server, project)
        container_regex = re.compile(r"^(cdi|virt)-.*-container")
        result: List[str] = []
        for package_name in package_list:
            if container_regex.match(package_name):
                result.append(package_name)
        return result

    def osc_get_products(self, project: str) -> List[str]:
        """
        Get all packages that belong to products being built in this project.

        :param project: The project to check for.
        :return: The list of packages that match the criteria. Might be empty.
        """
        package_list = core.meta_get_packagelist(self.osc_server, project)
        products_regex = re.compile(rf"^{self.convert_project_to_product(project)}")
        result: List[str] = []
        for package_name in package_list:
            if products_regex.match(package_name) and "release" not in package_name:
                result.append(package_name)
        return result

    def osc_get_jsc_from_sr(self, sr_number: int) -> List[str]:
        """
        Get all jsc's from a single Submit Request in the Open Build Service.

        :param sr_number: The submit request number that should be checked.
        :return: The list of jsc's that were mentioned.
        """
        issues = core.get_request_issues(self.osc_server, str(sr_number))
        result = []
        for issue in issues:
            if issue.get("tracker") == "jsc":
                result.append(issue.get("name"))
        return result

    def osc_do_release(
        self,
        project: str,
        package: str = "",
        repo: str = "",
        target_project: str = "",
        target_repository: str = "",
        no_delay: bool = False,
    ) -> None:
        """
        Perform a release for a given project.

        :param project: The project to release.
        :param package: Release only a specific package.
        :param repo: The repository that should be published.
        :param target_project: The target project where to release to.
        :param target_repository: The target repository where to release to.
        :param no_delay: If the action should be regularly scheduled or if it should be performed immediately
        """
        # pylint: disable=R0913
        baseurl = ["source", project]
        query = {"cmd": "release"}
        if package:
            baseurl.append(package)
        if repo:
            query["repository"] = repo
        if target_project:
            query["target_project"] = target_project
        if target_repository:
            query["target_repository"] = target_repository
        if no_delay:
            query["nodelay"] = "1"
        url = core.makeurl(self.osc_server, baseurl, query=query)
        fp_post_result = core.http_POST(url)
        while True:
            buf = fp_post_result.read(16384)
            if not buf:
                break
            sys.stdout.write(core.decode_it(buf))


class OscReleaseHelper(OscUtils):
    """
    Helper class to deduplicate between the different release scripts.
    """

    def release_to_common(self, project: str) -> None:
        """
        This consolidates common steps that are required to release a project. Specifics should be implemented in
        ``release_repo_to_<target>``.

        :param project: The project that will be released.
        """
        time.sleep(60)
        while not self.osc_is_repo_published(project, "containers"):
            print("containers: PENDING")
            time.sleep(60)
        if self.osc_is_repo_published(project, "containers"):
            print("containers: PUBLISHED")
        while not self.osc_is_repo_published(project, "images"):
            print("images: PENDING")
            time.sleep(60)
        if self.osc_is_repo_published(project, "images"):
            print("images: PUBLISHED")

    def release_repo_to_test(self, project: str) -> None:
        """
        Releases a ``:GA`` to ``:GA:TEST``. This is a synchronous call that will block until it is done.

        :param project: The project including the ``:GA`` suffix.
        """
        for container in self.osc_get_containers(project):
            self.osc_do_release(
                project,
                package=container,
                repo="containerfile",
                target_project=f"{project}:TEST",
                target_repository="containers",
            )
        self.osc_do_release(
            project,
            "sles15-image",
            repo="images",
            target_project=f"{project}:TEST",
            target_repository="containers",
        )
        products = self.osc_get_products(project)
        if products == "":
            print("[WARNING] There is no cloud image to be released")
        products.insert(0, "000product")
        products.insert(0, "kiwi-templates-Minimal")
        for product in products:
            self.osc_do_release(project, package=product)
        self.release_to_common(f"{project}:TEST")

    def release_repo_to_publish(self, project: str) -> None:
        """
        Releases a ``:GA:TEST`` to ``:GA:PUBLISH``. This is a synchronous call that will block until it is done.

        :param project: The project including the ``:GA`` suffix.
        """
        self.osc_do_release(f"{project}:TEST")
        self.release_to_common(f"{project}:GA:PUBLISH")
