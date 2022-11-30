build:
	python3 setup.py build

install:
	python3 setup.py install

sdist: build
	python3 setup.py sdist

rpm: sdist
	@mkdir -p rpm-build
	@cp dist/*.tar.gz rpm-build/
	rpmbuild \
	--define='_topdir %(pwd)/rpm-build' \
	--define='_builddir %{_topdir}' \
	--define='_rpmdir %{_topdir}' \
	--define='_srcrpmdir %{_topdir}' \
	--define='_specdir %{_topdir}' \
	--define='_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm' \
	--define='_sourcedir  %{_topdir}' \
	-ba sle-prjmgr-tools.spec

clean:
	@rm -r rpm-build build dist *.egg-info

podman-rpm-builder:
	@podman build -f docker/build.dockerfile -t localhost/sle-prjmgr-tools-builder:latest .
	@podman run -it --rm -v $(CURDIR):/code localhost/sle-prjmgr-tools-builder:latest

podman-rpm-install-check:
	@podman build -f docker/install-check.dockerfile -t localhost/sle-prjmgr-tools-install-check:latest .
	@podman run -it --rm -v $(CURDIR)/rpm-build:/rpms localhost/sle-prjmgr-tools-install-check:latest
