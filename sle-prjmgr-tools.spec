#
# spec file for package test
#
# Copyright (c) 2022 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#

%define sdist_name sle_prjmgr_tools

Name:           sle-prjmgr-tools
Version:        0.0.5
Release:        0
Summary:        SUSE SLE release management tools
License:        EUPL-1.2
URL:            https://github.com/openSUSE/sle-prjmgr-tools
Source:         %{name}-%{version}.tar.gz
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python-rpm-macros
Requires:       python3-requests
Requires:       python3-importlib-resources
Requires:       python3-PyYAML
Requires:       python3-jira
Requires:       python3-lxml
Requires:       osc
Recommends:     python3-keyring

%description
SUSE SLE release management tools that help publish Service Packs and Snapshots.

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build

%install
%py3_install

%post
%postun

%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{python3_sitelib}/%{sdist_name}/
%{python3_sitelib}/%{sdist_name}-*

%changelog
