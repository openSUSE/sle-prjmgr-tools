"""
This script retrieves all repositories for each incident it is given. The datasource is the SUSE internal SMELT tool.
"""

from typing import List

import requests

QUERY = """
query {{
  incidents(incidentId:{}) {{
    edges {{
      node {{
        repositories {{
          edges {{
            node {{
              name
            }}
          }}
        }}
      }}
    }}
  }}
}}
"""


def build_parser(parent_parser):
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.

    :param parent_parser: The subparsers object from argparse.
    """
    subparser = parent_parser.add_parser("incident_repos", help="incident_repos help")
    subparser.add_argument(
        "--smelt-api",
        dest="smelt_api",
        help="URL to the SMELT API.",
        default="https://smelt.suse.de/graphql/",
    )
    subparser.add_argument(
        "incidents",
        metavar="incident",
        help="The incident numbers",
        nargs="+",
        type=int,
    )
    subparser.set_defaults(func=main_cli)


def get_incident_repos(smelt_api_url: str, iid: int, timeout=180):
    """
    Retrieve all repositories that are affected by a single incident.

    :param smelt_api_url: The URL where the SMELT GraphQL API is present.
    :param iid: The incident ID.
    :param timeout: The timeout that is used for the SMELT API.
    :return: The set of repositories that is affected.
    """
    query = {"query": QUERY.format(iid)}
    results = requests.post(smelt_api_url, query, timeout=timeout).json()

    incs_repos = [
        i["node"]["repositories"]["edges"]
        for i in results["data"]["incidents"]["edges"]
    ]
    repos = set()
    for inc_repos in incs_repos:
        repos.update({s["node"]["name"] for s in inc_repos})

    return repos


def main(smelt_api_url: str, incidents: List[int]):
    """
    Main routine executes the non-CLI related logic.

    :param smelt_api_url: The URL where the SMELT GraphQL API is present.
    :param incidents: The list of incidents that should be looked up.
    """
    for iid in incidents:
        print(f"{iid}:")
        for repo in get_incident_repos(smelt_api_url, iid):
            print(f"  * {repo}")


def main_cli(args):
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    main(args.smelt_api, args.incidents)
