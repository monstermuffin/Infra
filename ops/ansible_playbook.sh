#!/usr/bin/env bash
# Convenience wrapper: cd into the ansible directory and run ansible-playbook.
set -euo pipefail

cd "$(cd "$(dirname "$0")/.." && pwd)/ansible"
exec ansible-playbook "$@"
