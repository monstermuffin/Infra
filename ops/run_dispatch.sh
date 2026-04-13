#!/bin/bash
set -euo pipefail

require_env() {
  local name=$1
  if [ -z "${!name:-}" ]; then
    echo "Required environment variable '$name' is not set" >&2
    exit 1
  fi
}

# Unlock git-crypt and write vault password file
require_env GIT_CRYPT_KEY
require_env VAULT_PASSWORD

printf '%s' "$GIT_CRYPT_KEY" | base64 -d | git-crypt unlock -

python3 - <<'PY'
from pathlib import Path
import subprocess
import sys

files = subprocess.run(
    ["git", "ls-files", "-z"],
    check=True,
    capture_output=True,
).stdout.decode().split("\0")

bad = []
for rel in files:
    if not rel:
        continue
    attr = subprocess.run(
        ["git", "check-attr", "filter", "--", rel],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if "filter: git-crypt" not in attr:
        continue
    path = Path(rel)
    if path.is_file() and path.read_bytes().startswith(b"\x00GITCRYPT\x00"):
        bad.append(rel)

if bad:
    print("git-crypt unlock did not decrypt these files:", file=sys.stderr)
    for rel in bad:
        print(f"  {rel}", file=sys.stderr)
    sys.exit(1)
PY

printf '%s\n' "$VAULT_PASSWORD" > /tmp/.vault_password
chmod 600 /tmp/.vault_password

SHA=$(git rev-parse HEAD)
LAST_SHA_FILE="/opt/github-runner/last_dispatched_sha"
LAST_SHA=$(cat "$LAST_SHA_FILE" 2>/dev/null || echo "")
export LAST_SUCCESSFUL_SHA="$LAST_SHA"

# Skip if already processed commit
if [ "$SHA" = "$LAST_SHA" ]; then
  echo "Skipping dispatch: commit $SHA already processed"
  exit 0
fi

GITHUB_REPO="monstermuffin/Infrastructure"
CONTEXT="ansible/dispatch"

post_status() {
  local state=$1
  local description=$2
  curl -s -X POST \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"state\":\"${state}\",\"context\":\"${CONTEXT}\",\"description\":\"${description}\"}" \
    "https://api.github.com/repos/${GITHUB_REPO}/statuses/${SHA}" \
    > /dev/null
}

post_status "pending" "Dispatch running..."

run_ansible() {
  python3 ops/dispatch.py && bash /tmp/dispatch_cmds.sh
}

run_terraform() {
  local tfvars_file
  tfvars_file=$(python3 ops/proxmox_vm_dispatch.py resolve-tfvars --base "${LAST_SUCCESSFUL_SHA:-}" --head "$SHA")
  python3 ops/gen_lxc_dns.py
  terraform -chdir=tf init -input=false
  if [ -n "$tfvars_file" ]; then
    terraform -chdir=tf apply -parallelism=1 -auto-approve -var-file="$tfvars_file"
  else
    terraform -chdir=tf apply -parallelism=1 -auto-approve
  fi
}

changed_vm_hosts() {
  if [ -n "$LAST_SUCCESSFUL_SHA" ] && git cat-file -e "${LAST_SUCCESSFUL_SHA}^{commit}" 2>/dev/null; then
    python3 ops/proxmox_vm_dispatch.py changed-names --base "$LAST_SUCCESSFUL_SHA" --head "$SHA"
  else
    python3 ops/proxmox_vm_dispatch.py changed-names --head "$SHA"
  fi
}

tf_files_changed() {
  # tf/ changes, or LXC inventory paths that gen_lxc_dns.py reads for DNS records
  local patterns=(tf/ ansible/inventory/group_vars/*/lxc/ ansible/inventory/host_vars/pve*/lxc/)
  if [ -n "$LAST_SUCCESSFUL_SHA" ] && git cat-file -e "${LAST_SUCCESSFUL_SHA}^{commit}" 2>/dev/null; then
    git diff --name-only "$LAST_SUCCESSFUL_SHA" "$SHA" -- "${patterns[@]}"
  else
    git diff-tree --no-commit-id -r --name-only "$SHA" -- "${patterns[@]}"
  fi
}

preflight_vm_check() {
  local base="${LAST_SUCCESSFUL_SHA:-}"
  local args=()
  if [ -n "$base" ] && git cat-file -e "${base}^{commit}" 2>/dev/null; then
    args+=(--base "$base")
  fi
  python3 ops/preflight_guest_check.py "${args[@]}" --head "$SHA"
}

run_vm_bootstrap() {
  local vm_limit
  vm_limit=$(changed_vm_hosts)

  if [ -z "$vm_limit" ]; then
    echo "No Terraform-managed VM definitions changed; skipping VM bootstrap"
    return 0
  fi

  echo "Bootstrapping Terraform-managed VMs: $vm_limit"
  (
    cd ansible
    mkdir -p /tmp/ansible-cp
    ANSIBLE_LOCAL_TEMP=/tmp \
    ANSIBLE_SSH_CONTROL_PATH_DIR=/tmp/ansible-cp \
    ansible-playbook playbooks/linux/manage.yml -e target="$vm_limit" --limit "$vm_limit"
  )
}

overall_status=0

if ! run_ansible; then
  overall_status=1
fi

if [ -n "$(tf_files_changed)" ]; then
  if ! preflight_vm_check; then
    overall_status=1
  elif ! run_terraform; then
    overall_status=1
  fi
else
  echo "No tf/ files changed; skipping Terraform"
fi

if [ "$overall_status" -eq 0 ] && ! run_vm_bootstrap; then
  overall_status=1
fi

if [ "$overall_status" -eq 0 ]; then
  echo "$SHA" > "$LAST_SHA_FILE"
  post_status "success" "Dispatch succeeded"
else
  post_status "failure" "Dispatch failed"
  exit 1
fi
