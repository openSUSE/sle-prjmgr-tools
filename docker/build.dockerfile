FROM registry.opensuse.org/opensuse/leap:15.4

RUN ["mkdir", "/code"]
RUN ["zypper", "in", "-y", "rpm-build", "python-rpm-macros", "python3-devel", "python3-setuptools"]

WORKDIR "/code"
VOLUME ["/code"]

CMD [ "make", "rpm" ]
