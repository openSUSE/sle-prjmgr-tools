#!/bin/sh

if [ $# -lt 2 ]; then
       echo "usage : package-updates-from-xcdchk.sh Build1 Build2  [SLE-xx-SPy] [ORIGIN_VERSION as SLE-xx-SPz]"
       exit 1
fi

BUILD1=${1/#Build/}
BUILD2=${2/#Build/}
VERSION=${3:-SLE-15-SP5}
ORIGIN_VERSION=${4:-SLE-15-SP5}

[ -r ChangeLog-$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2 ] || wget http://xcdchk.suse.de/raw/$VERSION-Full-Test/$BUILD2/all/ChangeLog-$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2  > /dev/null
[ -r $ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-updated-RPMs ] || wget http://xcdchk.suse.de/raw/$VERSION-Full-Test/$BUILD2/all/$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-updated-RPMs > /dev/null
[ -r $ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-new-RPMs ] || wget http://xcdchk.suse.de/raw/$VERSION-Full-Test/$BUILD2/all/$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-new-RPMs > /dev/null 
[ -r $ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-missing-RPMs ] || wget http://xcdchk.suse.de/raw/$VERSION-Full-Test/$BUILD2/all/$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-missing-RPMs > /dev/null
[ -r $ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-downgraded-RPMs ] || wget http://xcdchk.suse.de/raw/$VERSION-Full-Test/$BUILD2/all/$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-downgraded-RPMs > /dev/null


echo "Updated packages: "
grep "^o Update" ChangeLog-$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2 | awk '{print $3}' | while read -r line; do grep "^$line\." $ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-updated-RPMs; done | sed 's/\..*:/:/' | sed 's/^/\* /' | uniq
grep "^o Added" ChangeLog-$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2 | awk '{print $3}' | while read -r line; do grep "^$line\." $ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-updated-RPMs; done | sed 's/\..*:/:/' | sed 's/^/\* /' | uniq

echo
echo "Added packages: "
grep "^o Added" ChangeLog-$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2 | awk '{print $3}' | while read -r line; do grep ^$line $ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-new-RPMs; done | sed -e 's/\(.*\)-\([^-]*\)\-\([^-]*\)\..*/\1 \2-\3/' | sed 's/^/\* /' | uniq
grep "^o Update" ChangeLog-$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2 | awk '{print $3}' | while read -r line; do grep ^$line $ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-new-RPMs; done | sed -e 's/\(.*\)-\([^-]*\)\-\([^-]*\)\..*/\1 \2-\3/' | sed 's/^/\* /' | uniq

echo
echo "Removed packages: "
cat $ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-missing-RPMs | grep 'x86_64\|noarch' | sed -e 's/-[^-]*\..*//' | egrep -v "^kernel|.*debugsource.*|.*debuginfo.*" | sed 's/^/\* /' | uniq

echo
echo "Downgraded packages: "
cat $ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2-downgraded-RPMs | sed 's/\..*:/:/' | sed 's/^/\* /' | uniq 

echo
echo "Mentioned bug references: "
cat ChangeLog-$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2 | while read -r line; do egrep -o '[bsc#|bnc#|boo#][0-9]{7}'; done | uniq | while read -r line; do egrep -o '[0-9]{7}'; done | sort | paste -s -d, -

echo
echo "Filter for resolved P1/P2 bugs with this build in SLE 15 SP5"
bugs=$(cat ChangeLog-$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2 | while read -r line; do egrep -o '[bsc#|bnc#|boo#][0-9]{7}'; done | uniq | while read -r line; do egrep -o '[0-9]{7}'; done | sort | sed ':a;N;$!ba;s/\n/%2C/g')
echo "https://bugzilla.suse.com/buglist.cgi?bug_id=${bugs}&bug_id_type=anyexact&bug_status=RESOLVED&bug_status=VERIFIED&columnlist=short_desc&priority=P1%20-%20Urgent&priority=P2%20-%20High&product=PUBLIC%20SUSE%20Linux%20Enterprise%20Desktop%2015%20SP5&product=PUBLIC%20SUSE%20Linux%20Enterprise%20High%20Availability%20Extension%2015%20SP5&product=PUBLIC%20SUSE%20Linux%20Enterprise%20HPC%2015%20SP5&product=PUBLIC%20SUSE%20Linux%20Enterprise%20Server%2015%20SP5&product=SUSE%20Linux%20Enterprise%20Desktop%2015%20SP5&product=SUSE%20Linux%20Enterprise%20High%20Availability%20Extension%2015%20SP5&product=SUSE%20Linux%20Enterprise%20HPC%2015%20SP5&product=SUSE%20Linux%20Enterprise%20HPC%2015%20SP5%20in%20Public%20Clouds&product=SUSE%20Linux%20Enterprise%20Server%2015%20SP5&product=SUSE%20Linux%20Enterprise%20Server%2015%20SP5%20in%20Public%20Clouds&product=SUSE%20Linux%20Enterprise%20Server%20for%20SAP%2015%20SP5%20in%20Public%20Clouds&product=SUSE%20Linux%20Enterprise%20Server%20for%20SAP%20Applications%2015%20SP5&query_based_on=SLE_15SP5_Resolved_issues&query_format=advanced&resolution=FIXED"

echo
echo "Mentioned JIRA references: "
cat ChangeLog-$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2 | egrep -o 'jsc#SLE-[0-9]{5}|jsc#PED-[0-9]{1,5}' | sort | uniq | paste -s -d, -

PED=$(cat ChangeLog-$ORIGIN_VERSION-Full-Test-Build$BUILD1-Build$BUILD2 | egrep -o 'PED-[0-9]{1,5}' | sort | uniq | paste -s -d, -)

echo
echo "JIRA query for incorrect state"
echo "=============================="
echo "Query:"
echo "------"
echo "issue in (${PED}) AND status NOT IN (\"QE Open\",\"QE In Progress\",\"QE Blocked\",\"Engineering Done\",\"Dev In Progress\",\"IBS Integration\") AND type = Implementation"
echo "Comment:"
echo "--------"
echo "A submit request referencing this feature has been merged into build${BUILD2}."
echo "Please update the state of this ticket, as it doesn't reflect the correct state of development."
echo "Labels:"
echo "-------"
echo "Add status:wait_for_status"
echo "Add status:code_merged"

echo
echo "JIRA query for still under development"
echo "======================================"
echo "Query:"
echo "------"
echo "issue in (${PED}) AND status = \"Dev In Progress\" AND type = Implementation"
echo "Comment:"
echo "--------"
echo "A submit request referencing this feature has been merged into build${BUILD2}."
echo "Labels:"
echo "-------"
echo "Remove status:wait_for_status"
echo "Add status:code_merged"

echo
echo "JIRA query for already completed features"
echo "========================================="
echo "Query:"
echo "------"
echo "issue in (${PED}) AND status IN (\"QE Open\",\"QE In Progress\",\"QE Blocked\",\"Engineering Done\") AND type = Implementation"
echo "Comment:"
echo "--------"
echo "A submit request referencing this feature has been merged into build${BUILD2}."
echo "Labels:"
echo "-------"
echo "no handling required, only remove stale \"status:\" labels"

echo
echo "JIRA query for features ready to transition"
echo "==========================================="
echo "Query:"
echo "------"
echo "issue in (${PED}) AND status = \"IBS Integration\" AND type = Implementation"
echo "Comment:"
echo "--------"
echo "A submit request referencing this feature has been merged into build${BUILD2}."
echo "Labels:"
echo "-------"
echo "Remove status:code_merged"
echo "Remove status:wait_for_status"
