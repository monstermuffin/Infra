#!/bin/bash
set -euo pipefail

TOKEN=$(infisical login --method=universal-auth \
  --client-id="$INFISICAL_UNIVERSAL_AUTH_CLIENT_ID" \
  --client-secret="$INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET" \
  --domain="$INFISICAL_API_URL" --plain --silent)

exec infisical secrets get ANSIBLE_VAULT_PASSWORD --token="$TOKEN" --projectId="$INFISICAL_PROJECT_ID" \
  --env="$INFISICAL_ENV_SLUG" --path=/ --plain --silent
