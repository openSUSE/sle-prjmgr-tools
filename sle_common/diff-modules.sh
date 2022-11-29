#!/usr/bin/env sh

#set -x

THIS=$(basename $0)

function usage() {
    echo "
    Usage:
    $THIS -f <from_projec> [-o <from_revision_number>] -t <to_project> [-d <to_revision_number>] 
    ex: $THIS -f 15-SP2 -t 15-SP3 -d 75
    "
    exit -1
}

FROM_REVISION=''
TO_REVISION=''

while getopts "f:t:o:d:" opt; do
    case $opt in
        f)
            FROM=SUSE:SLE-$OPTARG:GA
            ;;
        t)
            TO=SUSE:SLE-$OPTARG:GA
            ;;
        o)
            FROM_REVISION="-r $OPTARG"
            ;;
        d)
            TO_REVISION="-r $OPTARG"
    esac
done

[ -z "${FROM}" -o -z "${TO}" ] && usage

FROM_GROUPS_FILE="groups_FROM.yml"
TO_GROUPS_FILE="groups_TO.yml"
CHANGES_GROUPS_FILE="Changes_from_${FROM}_to_${TO}.diff"

osc -A https://api.suse.de/ checkout ${FROM} 000package-groups groups.yml ${FROM_REVISION}
mv -v groups.yml ${FROM_GROUPS_FILE}
osc -A https://api.suse.de/ checkout ${TO} 000package-groups groups.yml ${TO_REVISION}
mv -v groups.yml ${TO_GROUPS_FILE}

# remove the JIRA, bug references and commented lines
sed -i -e 's/\s*#.*$//' ${FROM_GROUPS_FILE}
sed -i -e 's/\s*#.*$//' ${TO_GROUPS_FILE}

# marked the modules in ${TO_GROUPS_FILE} to make difference
sed -i -e 's/\(^[a-zA-Z_]*:$\)/ \1/g' ${TO_GROUPS_FILE}

diff --suppress-common-lines --ignore-blank-lines --ignore-trailing-space ${FROM_GROUPS_FILE} ${TO_GROUPS_FILE} > ${CHANGES_GROUPS_FILE}

rm -vf ${FROM_GROUPS_FILE}
rm -vf ${TO_GROUPS_FILE}

# remove the line numbers
sed -i -e '/^[0-9].*$/d' ${CHANGES_GROUPS_FILE}

# remove ---
sed -i -e '/^---$/d' ${CHANGES_GROUPS_FILE}

# remove the repetitions in module names
sed -i -e '/< [a-zA-Z_]*:$/d' ${CHANGES_GROUPS_FILE}

# remove the empty lines
sed -i -e '/^[<>]\s*$/d' ${CHANGES_GROUPS_FILE}

# mark removed packages with -
sed -i -e 's/^<\s*-/-  /' ${CHANGES_GROUPS_FILE}

# mark added packages with +
sed -i -e 's/^>\s*-/+  /' ${CHANGES_GROUPS_FILE}

# mark removed from module names
sed -i -e 's/^[<>]\s\s//' ${CHANGES_GROUPS_FILE}

# remove lines not related with modules
sed -i '/^UNWANTED:/,$!d' ${CHANGES_GROUPS_FILE} 

echo ${CHANGES_GROUPS_FILE}
