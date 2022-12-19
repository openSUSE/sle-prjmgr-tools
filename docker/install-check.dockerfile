FROM registry.opensuse.org/opensuse/leap:15.4

RUN [ \
    "zypper", \
    "in", \
    "-y", \
    "python3-requests", \
    "python3-PyYAML", \
    "python3-jira", \
    "python3-lxml", \
    "python3-importlib_resources", \
    "python3-keyring", \
    "python3-argcomplete", \
    "osc" \
]

WORKDIR "/rpms"
VOLUME ["/rpms"]

# We don't know the exact name of the RPM. Thus we need a command line to expand the wildcard.
CMD ["/bin/sh", "-c", "zypper in -y --allow-unsigned-rpm *.rpm && echo '---' && sle-prjmgr-tools -h"]
