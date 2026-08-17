#!/bin/bash
set -euo pipefail

DIR="${RUNTIME_DIRECTORY:-/run/ccagent-secrets}"

TOKEN=$(infisical login --method=universal-auth \
  --client-id="$INFISICAL_UNIVERSAL_AUTH_CLIENT_ID" \
  --client-secret="$INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET" \
  --domain="$INFISICAL_API_URL" --plain --silent)

infisical secrets get GH_APP_PRIVATE_KEY --token="$TOKEN" --projectId="$INFISICAL_PROJECT_ID" \
  --env="$INFISICAL_ENV_SLUG" --path=/ --plain --silent > "$DIR/github-app-private-key.pem"
infisical secrets get ANSIBLE_SSH_KEY --token="$TOKEN" --projectId="$INFISICAL_PROJECT_ID" \
  --env="$INFISICAL_ENV_SLUG" --path=/ --plain --silent > "$DIR/ansible_ccagent"

chmod 0600 "$DIR/github-app-private-key.pem" "$DIR/ansible_ccagent"
