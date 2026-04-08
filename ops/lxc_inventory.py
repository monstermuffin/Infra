#!/usr/bin/env python3
# Check LXC inventory for dupe VMID/hostname/IP.

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not available.", file=sys.stderr)
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
LXC_GLOBS = (
    "ansible/inventory/group_vars/*/lxc/**/*.yml",
    "ansible/inventory/host_vars/pve*/lxc/*.yml",
)


yaml.add_multi_constructor(
    "",
    lambda loader, tag, node: loader.construct_scalar(node),
    Loader=yaml.SafeLoader,
)


def find_lxc_files() -> list[Path]:
    files: list[Path] = []
    for pattern in LXC_GLOBS:
        files.extend(REPO_ROOT.glob(pattern))
    return sorted(files)


def _ip_without_prefix(value: str) -> str:
    return value.split("/", 1)[0].strip()


def _scope_for_path(path: Path) -> str:
    parts = path.parts
    if "group_vars" in parts:
        idx = parts.index("group_vars")
        if idx + 1 < len(parts):
            return f"group:{parts[idx + 1]}"
    if "host_vars" in parts:
        idx = parts.index("host_vars")
        if idx + 1 < len(parts):
            return f"host:{parts[idx + 1]}"
    return "unknown"


def collect_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []

    for path in find_lxc_files():
        try:
            with path.open() as handle:
                data = yaml.safe_load(handle) or {}
        except Exception as exc:
            print(f"WARNING: skipping {path.relative_to(REPO_ROOT)}: {exc}", file=sys.stderr)
            continue

        for key, value in data.items():
            if not key.startswith("pve_lxcs_") or not isinstance(value, dict):
                continue

            for lxc_name, lxc in value.items():
                if not isinstance(lxc, dict):
                    continue

                records.append(
                    {
                        "scope": _scope_for_path(path),
                        "name": str(lxc_name),
                        "vmid": str(lxc.get("vmid", "")),
                        "hostname": str(lxc.get("hostname", "")),
                        "node": str(lxc.get("node", "")),
                        "network_ip": str(lxc.get("network_ip", "")),
                        "network_ip_plain": _ip_without_prefix(str(lxc.get("network_ip", ""))) if lxc.get("network_ip") else "",
                        "network_vlan": str(lxc.get("network_vlan", "")),
                        "source": str(path.relative_to(REPO_ROOT)),
                    }
                )

    return sorted(records, key=lambda record: (record["vmid"], record["hostname"], record["name"]))


def find_duplicates(records: list[dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    checks = {
        "vmid": defaultdict(list),
        "hostname": defaultdict(list),
        "network_ip_plain": defaultdict(list),
    }

    for record in records:
        vmid = record.get("vmid", "").strip()
        if vmid:
            checks["vmid"][(record.get("scope", ""), vmid)].append(record)

        for field in ("hostname", "network_ip_plain"):
            value = record.get(field, "").strip()
            if value:
                checks[field][value].append(record)

    duplicates: dict[str, list[dict[str, object]]] = {}
    for field, bucket in checks.items():
        entries = []
        for value, items in sorted(bucket.items()):
            if len(items) > 1:
                display_value = value[1] if field == "vmid" and isinstance(value, tuple) else value
                scope = value[0] if field == "vmid" and isinstance(value, tuple) else None
                entries.append(
                    {
                        "value": display_value,
                        "scope": scope,
                        "items": [
                            {
                                "scope": item["scope"],
                                "name": item["name"],
                                "hostname": item["hostname"],
                                "vmid": item["vmid"],
                                "network_ip": item["network_ip"],
                                "source": item["source"],
                            }
                            for item in items
                        ],
                    }
                )
        duplicates[field] = entries

    return duplicates


def print_table(records: list[dict[str, str]]) -> None:
    columns = [
        ("scope", "Scope"),
        ("vmid", "VMID"),
        ("network_ip_plain", "IP"),
        ("network_vlan", "VLAN"),
        ("node", "Node"),
        ("name", "Name"),
        ("hostname", "Hostname"),
        ("source", "Source"),
    ]
    widths = {
        key: max(len(label), *(len(record.get(key, "")) for record in records))
        for key, label in columns
    }

    header = "  ".join(label.ljust(widths[key]) for key, label in columns)
    print(header)
    print("  ".join("-" * widths[key] for key, _ in columns))
    for record in records:
        print("  ".join(record.get(key, "").ljust(widths[key]) for key, _ in columns))


def print_duplicates(duplicates: dict[str, list[dict[str, object]]]) -> None:
    labels = {
        "vmid": "Duplicate VMIDs",
        "hostname": "Duplicate hostnames",
        "network_ip_plain": "Duplicate IPs",
    }

    any_duplicates = False
    for field in ("vmid", "hostname", "network_ip_plain"):
        entries = duplicates.get(field, [])
        print(f"{labels[field]}:")
        if not entries:
            print("  none")
            continue

        any_duplicates = True
        for entry in entries:
            items = ", ".join(
                f"{item['name']} [{item['source']}]"
                for item in entry["items"]
            )
            prefix = f"{entry['scope']} / " if entry.get("scope") else ""
            print(f"  {prefix}{entry['value']}: {items}")

    if not any_duplicates:
        print("No duplicate identifiers found.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect and validate LXC inventory.")
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for the inventory listing.",
    )
    parser.add_argument(
        "--check-duplicates",
        action="store_true",
        help="Exit non-zero when duplicate VMIDs, hostnames, or IPs are found.",
    )
    args = parser.parse_args()

    records = collect_records()
    duplicates = find_duplicates(records)

    if args.format == "json":
        print(json.dumps({"records": records, "duplicates": duplicates}, indent=2))
    else:
        print_table(records)
        print("")
        print_duplicates(duplicates)

    if args.check_duplicates and any(duplicates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
