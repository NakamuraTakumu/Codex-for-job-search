#!/usr/bin/env bash
#
# Usage:
#   ./tool/setup_git_hooks.sh
#
# Purpose:
#   Configure this repository to use the versioned hooks under .githooks/.

set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
chmod +x tool/rotate_document_before_commit.sh
chmod +x tool/setup_git_hooks.sh

echo "Configured core.hooksPath=.githooks"
