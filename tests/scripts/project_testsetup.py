"""
This scripts sets up an environment in an Open Build Service and JIRA instance.

Botmaster:

- gocd instance that is configured with this script
- Required to run against test project:
  - SLE15.SP5.Stagings.RelPkgs
  - SLE15.SP5.Staging.A

OBS requirements:

- The OSC Client ist installed and able to authenticate non-interactively.
- Project structure must be: ``...:SLE-<digits>-SP<digit>:GA:<|TEST|PUBLISHED>``
- The projects must have two repositories "containers" and "images".

JIRA requirements:

- PAT (= Personal Access Token) authentication
- User must be able to write comments on tickets
- User must be able to move a ticket via the transition "Integrated" towards the next state.
- The issue type "Implementation" must be known to the JIRA instance
- The following status must be known to the JIRA instance:
  - QE Open
  - QE In Progress
  - QE Blocked
  - Engineering Done
  - In Maintenance
  - Dev In Progress
  - IBS Integration

After these requirements are met this script can be executed.
"""
from osc import core

project = {
    "source": "SUSE:SLE-15-SP5:GA",
    "target": "home:SchoolGuy:SLE-15-SP5:GA",
}

# Meta taken from real projects and release targets adjusted

# OBS: Create project structure
# OBS: Create META for GA:PUBLISH
# OBS: Create META for GA:TEST
# OBS: Create META for GA

# Do Staging Setup
