#!/bin/sh
# Prints true when a file whose path matches the extended regular expression $1 changed between the commit in
# $BASE and HEAD, and false otherwise. The CI workflows run their check jobs only when it prints true: a job
# skipped by its condition reports success, while a workflow skipped by path filters never reports, which
# would leave a required check waiting.
#
# Without a usable base, such as an empty or unknown commit, it prints true so that the check runs.
set -eu

pattern=$1
base=${BASE:-}

if [ -z "$base" ] || [ "$base" = "0000000000000000000000000000000000000000" ] ||
	! git cat-file -e "${base}^{commit}" 2>/dev/null; then
	echo true
	exit 0
fi

# Three dots compare HEAD with the merge base, so changes that reached the base branch meanwhile do not count.
if git diff --name-only "${base}...HEAD" | grep -qE "$pattern"; then
	echo true
else
	echo false
fi
