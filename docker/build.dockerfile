FROM registry.opensuse.org/opensuse/tumbleweed:latest

RUN ["mkdir", "/code"]
RUN [ \
    "zypper", \
    "in", \
    "-y", \
    "rpm-build", \
    "python-rpm-macros", \
    "python3-devel", \
    "python3-setuptools", \
    "python3-argcomplete" \
]

WORKDIR "/code"
VOLUME ["/code"]

CMD [ "make", "rpm" ]
