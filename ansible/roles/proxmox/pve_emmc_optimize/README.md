# pve_emmc_optimize

Reduce eMMC write operations on Proxmox VE hosts to prolong storage lifespan.

Only for hosts with eMMC storage — unofficial Proxmox config, not for production. Requires external disk/NFS for log and RRD relocation.

Based on:
- https://ibug.io/blog/2023/07/prolonging-emmc-life-span-with-proxmox-ve/
- https://fat-nerds.com/dot-nerd/cut-down-proxmox-ve-emmc-sd-read-write/

## Optimizations

- **Swap**: Disable entirely (for 16GB+ RAM hosts)
- **Logs**: Move `/var/log` to external disk
- **RRD**: Reduce write frequency (30min intervals) and/or relocate to external disk
- **Filesystem**: Add `noatime`, `nodiratime`, `commit=600` to root mount

Intentionally excluded: stopping HA services, pvestatd, firewall logger, tmpfs logs — all cause more problems than they solve.

## Lifespan context

Proxmox writes ~1.5-4.5 TB/year. Most eMMC handles 10-20 TB total (1000 P/E cycles for TLC). Light workloads may last 5-10+ years without optimizations.

## Variables

See [defaults/main.yml](defaults/main.yml). Key ones:

```yaml
pve_emmc_optimize_enabled: false    # must be true per-host
pve_emmc_optimize_state: "present"  # "present", "absent", or ""

pve_emmc_optimize_swap_disable: true
pve_emmc_optimize_logs_disk: ""         # e.g. "/dev/sdb1"
pve_emmc_optimize_rrd_mode: "timeout"   # "timeout", "relocate", "both"
pve_emmc_optimize_rrd_disk: ""
pve_emmc_optimize_filesystem_opts: true
pve_emmc_optimize_monitoring: true
```

## Tags

- `info`, `monitoring`, `stats` — health info only
- `apply`, `optimize` — apply optimizations
- `swap`, `logs`, `rrd`, `filesystem` — individual optimizations
- `revert`, `restore` — revert all

## Usage

```bash
# Check eMMC health
ansible-playbook playbooks/pve/emmc_optimize.yml --tags monitoring

# Apply all
ansible-playbook playbooks/pve/emmc_optimize.yml

# Specific optimizations only
ansible-playbook playbooks/pve/emmc_optimize.yml --tags swap,filesystem

# Dry run
ansible-playbook playbooks/pve/emmc_optimize.yml --check --diff

# Revert
ansible-playbook playbooks/pve/emmc_optimize.yml --tags revert
```

## Host config example

```yaml
# host_vars/mini-pc-01.yml
pve_emmc_optimize_enabled: true
pve_emmc_optimize_logs_disk: "/dev/sdb1"
pve_emmc_optimize_rrd_mode: "both"
pve_emmc_optimize_rrd_disk: "/dev/sdb2"
```

## Reverting

Fully reversible. Backups stored in `/root/emmc-optimize-backups/` with timestamps. Swap revert recreates an 8G LV. Log/RRD revert unmounts external disk (old data remains on it). Filesystem revert restores original fstab.
