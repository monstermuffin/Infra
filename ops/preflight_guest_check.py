#!/usr/bin/env python3
"""Pre-flight checks before Proxmox guest Terraform deployments.

For each planned guest (added or modified in the current commit):
  - Verifies the guest ID is not already claimed by any existing guest in the
    cluster (catches conflicts with LXC containers and other VMs by name).
  - Pings the planned IP to confirm it is not already in use on the network.

Exits 0 when all clear, 1 when any conflict is detected.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not available.", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
GUEST_ROOT = REPO_ROOT / "tf" / "proxmox_vms"
CONTROL_PLANES_FILE = REPO_ROOT / "ops" / "proxmox_control_planes.yml"


# ---------------------------------------------------------------------------
# Control plane helpers
# ---------------------------------------------------------------------------

def _load_control_planes() -> list[dict]:
    raw = yaml.safe_load(CONTROL_PLANES_FILE.read_text()) or {}
    return raw.get("control_planes", [])


def _api_node_for_plane(plane: dict) -> str:
    """Derive the SSH hostname for the first node in a control plane."""
    node = plane["nodes"][0]
    suffix = plane["hostname_suffixes"][0]  # e.g. ".aah.muffn.io"
    return f"{node}{suffix}"


def _match_plane(doc: dict, control_planes: list[dict]) -> dict | None:
    node_name = doc.get("node_name", "")
    hostname = doc.get("hostname", "")
    for plane in control_planes:
        if node_name in plane["nodes"] and any(
            hostname.endswith(s) for s in plane["hostname_suffixes"]
        ):
            return plane
    return None


# ---------------------------------------------------------------------------
# Guest definition helpers
# ---------------------------------------------------------------------------

def _changed_guest_files(base: str | None, head: str) -> list[Path]:
    if base:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", base, head, "--", "tf/proxmox_vms"],
            cwd=REPO_ROOT, text=True, capture_output=True, check=True,
        )
        paths = [REPO_ROOT / line for line in result.stdout.splitlines() if line.strip()]
        return [p for p in paths if p.suffix == ".yml" and p.is_file()]
    return sorted(GUEST_ROOT.rglob("*.vm.yml"))


def _guest_ip(doc: dict) -> str | None:
    addr = doc.get("network", {}).get("ipv4_address", "")
    return addr.split("/")[0] if addr else None


# ---------------------------------------------------------------------------
# Proxmox cluster query (via SSH to a cluster node)
# ---------------------------------------------------------------------------

def _cluster_guests(api_node: str) -> list[dict]:
    """Return the full /cluster/resources list from a Proxmox node via SSH."""
    try:
        result = subprocess.run(
            [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=10",
                "-o", "BatchMode=yes",
                f"root@{api_node}",
                "pvesh get /cluster/resources --output-format json",
            ],
            capture_output=True, text=True, check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: SSH to {api_node} failed: {exc.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Could not parse pvesh output from {api_node}: {exc}", file=sys.stderr)
        sys.exit(1)


def _build_guest_id_map(guests: list[dict]) -> dict[int, dict]:
    """Map guest ID → resource dict for every guest that has a vmid."""
    mapping: dict[int, dict] = {}
    for g in guests:
        raw = g.get("vmid")
        if raw is None:
            continue
        try:
            guest_id = int(raw)
        except (TypeError, ValueError):
            continue
        mapping[guest_id] = g
    return mapping


# ---------------------------------------------------------------------------
# IP ping check
# ---------------------------------------------------------------------------

def _ping(ip: str) -> bool:
    """Return True if the IP responds to a single ping within 1 second."""
    result = subprocess.run(
        ["ping", "-c", "1", "-W", "1", ip],
        capture_output=True,
    )
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Main check logic
# ---------------------------------------------------------------------------

def run_checks(base: str | None, head: str) -> int:
    control_planes = _load_control_planes()
    guest_files = _changed_guest_files(base, head)

    if not guest_files:
        print("No guest definitions changed; skipping pre-flight checks.")
        return 0

    print(f"Running pre-flight checks for {len(guest_files)} guest definition(s)...\n")

    # Group files by control plane so we make one SSH call per cluster.
    by_plane: dict[str, tuple[dict, list[tuple[Path, dict]]]] = {}
    unmatched: list[Path] = []

    for path in guest_files:
        doc = yaml.safe_load(path.read_text()) or {}
        plane = _match_plane(doc, control_planes)
        if plane is None:
            unmatched.append(path)
            continue
        pid = plane["id"]
        if pid not in by_plane:
            by_plane[pid] = (plane, [])
        by_plane[pid][1].append((path, doc))

    if unmatched:
        for p in unmatched:
            print(f"  WARNING: {p.relative_to(REPO_ROOT)} does not match any control plane; skipping.")

    failures: list[str] = []

    for plane_id, (plane, guests) in by_plane.items():
        api_node = _api_node_for_plane(plane)
        print(f"Cluster: {plane_id}  (querying {api_node})")

        cluster_guests = _cluster_guests(api_node)
        guest_id_map = _build_guest_id_map(cluster_guests)

        for path, doc in guests:
            name = doc.get("name") or path.stem.removesuffix(".vm")
            planned_id = doc.get("vm_id")
            planned_ip = _guest_ip(doc)
            rel = path.relative_to(REPO_ROOT)

            print(f"  {rel}  (guest_id={planned_id}, ip={planned_ip})")

            # --- Guest ID conflict check ---
            if planned_id is not None and planned_id in guest_id_map:
                existing = guest_id_map[planned_id]
                existing_type = existing.get("type", "?")
                existing_name = existing.get("name", "?")
                existing_node = existing.get("node", "?")

                # Same ID, same name, same type → guest already exists (update path, no conflict)
                if existing_type == "qemu" and existing_name == name:
                    print(f"    guest_id {planned_id}: exists as this guest on {existing_node} (update)")
                else:
                    msg = (
                        f"    CONFLICT: guest_id {planned_id} is already in use by "
                        f"{existing_type}/{existing_name} on {existing_node}"
                    )
                    print(msg)
                    failures.append(f"{rel}: {msg.strip()}")
            else:
                print(f"    guest_id {planned_id}: free ✓")

                # --- IP ping check (only for new guests, not updates) ---
                if planned_ip:
                    if _ping(planned_ip):
                        msg = f"    CONFLICT: {planned_ip} responds to ping — IP already in use"
                        print(msg)
                        failures.append(f"{rel}: {msg.strip()}")
                    else:
                        print(f"    ip {planned_ip}: no ping response ✓")

        print()

    if failures:
        print("Pre-flight checks FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1

    print("Pre-flight checks passed.")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-flight checks for Proxmox guest deployments.")
    parser.add_argument("--base", default=None, help="Git base SHA. If omitted, all guest definitions are checked.")
    parser.add_argument("--head", default="HEAD", help="Git head SHA (default: HEAD).")
    args = parser.parse_args()
    return run_checks(args.base, args.head)


if __name__ == "__main__":
    sys.exit(main())
