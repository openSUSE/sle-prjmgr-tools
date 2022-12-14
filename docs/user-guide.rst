**********
User Guide
**********

This page gives a longer explanation what the different scriptlets are doing. A short summary can be found in the help
of the tool itself.

.. code-block:: shell

   sle-prjmgr-tools -h  # Help of the full tool
   sle-prjmgr-tools <name> -h  # Help of each scriptlet.


In case you encounter any issues please open a bug on GitHub:
`GitHub Issues - openSUSE/sle-prjmgr-tools <https://github.com/openSUSE/sle-prjmgr-tools/issues/new/choose>`_

Shell Completion
################

Bash
====

Add the following line to your ``~/.bashrc`` manually please:

.. code-block:: shell

   eval "$(register-python-argcomplete my-awesome-script)"


If the file does not exist please create it with:

.. code-block:: shell

   touch ~/.bashrc


ZSH
===

Please execute the following code snippet:

.. code-block:: shell

   autoload -U bashcompinit
   bashcompinit


After you have done this please follow the instructions for Bash.

Fish
====

Please execute the following commands in a fish terminal:

.. code-block:: shell

   register-python-argcomplete --shell fish my-awesome-script > ~/.config/fish/completions/sle-prjmgr-tools.fish


Diff Modules
############

.. note:: This documentation is a work in progress. Please give it some love and open a PR to fill this section with
          content.

Incident Repos
##############

.. note:: This documentation is a work in progress. Please give it some love and open a PR to fill this section with
          content.

Jira Epics
##########

This script will search through all changelogs of a project and list all JIRA issues that are mentioned. The script
will include also the revision history in the scanning process in addition to the changelogs.

The syntax of such a mention is ``jsc#KEY-9999``.

List accepted Packages
######################

.. note:: This documentation is a work in progress. Please give it some love and open a PR to fill this section with
          content.

Package updates from XCDCHK
###########################

.. note:: This documentation is a work in progress. Please give it some love and open a PR to fill this section with
          content.

Packagelist Report
##################

.. note:: This documentation is a work in progress. Please give it some love and open a PR to fill this section with
          content.

Release To
##########

.. note:: This documentation is a work in progress. Please give it some love and open a PR to fill this section with
          content.

Search Binary
#############

.. note:: This documentation is a work in progress. Please give it some love and open a PR to fill this section with
          content.

SLE Build
#########

.. note:: This documentation is a work in progress. Please give it some love and open a PR to fill this section with
          content.

Update Build Status Page
########################

.. note:: This documentation is a work in progress. Please give it some love and open a PR to fill this section with
          content.
