#!/usr/bin/env python3
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_jwt(app_id: str, key_path: str) -> str:
    now = int(time.time())
    header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    # iat backdated and exp capped short per GitHub's clock-drift/max-lifetime guidance
    payload = b64url(json.dumps({"iat": now - 60, "exp": now + 540, "iss": app_id}).encode())
    signing_input = f"{header}.{payload}".encode()
    signature = subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", key_path],
        input=signing_input,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    return f"{header}.{payload}.{b64url(signature)}"


def installation_token(app_id: str, installation_id: str, key_path: str) -> str:
    jwt = make_jwt(app_id, key_path)
    req = urllib.request.Request(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        method="POST",
        headers={
            "Authorization": f"Bearer {jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)["token"]
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"github-app-token: request failed: {e.code} {e.read().decode()}\n")
        sys.exit(1)


def main() -> None:
    app_id = os.environ["GH_APP_ID"]
    installation_id = os.environ["GH_APP_INSTALLATION_ID"]
    key_path = os.environ["GH_APP_PRIVATE_KEY_PATH"]
    print(installation_token(app_id, installation_id, key_path))


if __name__ == "__main__":
    main()
