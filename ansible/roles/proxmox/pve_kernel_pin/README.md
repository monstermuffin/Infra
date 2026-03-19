# pve_kernel_pin

Pin/unpin PVE kernels using `proxmox-boot-tool`. Pinning prevents kernel changes during upgrades.

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `pve_kernel_pin_version` | `""` | Version to pin (e.g. `6.8.12-1`). Empty string unpins |
| `pve_kernel_pin_auto_reboot` | `false` | Reboot after pin change |

## Tags

| Tag | Description |
|-----|-------------|
| `info` | Show kernel info only |
| `pin` | Pin a kernel version |
| `unpin` | Unpin |
| `reboot` | Reboot (if auto_reboot enabled) |

## Examples

```bash
# Check current state
ansible-playbook playbooks/pve/kernel_pin.yml --tags info

# Pin/unpin (set version in group_vars or pass as extra var)
ansible-playbook playbooks/pve/kernel_pin.yml --tags pin -e pve_kernel_pin_version=6.8.12-1
ansible-playbook playbooks/pve/kernel_pin.yml --tags unpin
```

Reboot required after pin changes take effect.
