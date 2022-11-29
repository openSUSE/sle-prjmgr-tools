"""
Retrieve the Channel, Project and Source Package for a list of given binaries.
"""

from typing import List

import requests

QUERY = """
query {{
  binaries(name_Iexact:"{}") {{
    edges {{
      node {{
        channelsources {{
          edges {{
            node {{
              channel {{
                name
              }}
              package {{
                name
              }}
              project {{
                name
              }}
            }}
          }}
        }}
      }}
    }}
  }}
}}
"""
SMELT_API = "https://smelt.suse.de/graphql/"


def build_parser(parent_parser):
    """
    Builds the parser for this script. This is executed by the main CLI dynamically.

    :param parent_parser: The subparsers object from argparse.
    """
    subparser = parent_parser.add_parser("search_binary", help="search_binary help")
    subparser.add_argument(
        "binaries", metavar="binary", help="The binary names", nargs="+"
    )
    subparser.set_defaults(func=main_cli)


def get_binary_info(binary: str, timeout=180):
    """
    Retrieve all channel, project and source package names for a given binary.

    :param binary: The name of the binaries that should be searched for.
    :param timeout: Timout when the connection should be aborted.
    :return: A Tuple with the name of the channel, project and source package is yielded.
    """
    query = {"query": QUERY.format(binary)}
    results = requests.post(SMELT_API, query, timeout=timeout).json()

    for bin_result in results["data"]["binaries"]["edges"]:
        for result in bin_result["node"]["channelsources"]["edges"]:
            yield (
                result["node"]["channel"]["name"],
                result["node"]["project"]["name"],
                result["node"]["package"]["name"],
            )


def main(binaries: List[str]):
    """
    Main routine executes the non-CLI related logic.

    :param binaries: The list of binaries that should be checked.
    """
    for binary in binaries:
        print(f"{binary}:")
        for chan, proj, pack in get_binary_info(binary):
            print(f" {chan}: {proj}/{pack}")


def main_cli(args):
    """
    Main routine that executes the script

    :param args: Argparse Namespace that has all the arguments
    """
    main(args.binaries)
