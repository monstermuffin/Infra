# pve_microcode

Install/update processor microcode on Proxmox VE hosts. Auto-detects Intel vs AMD, downloads packages directly from Debian non-free-firmware repos.

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `pve_microcode_action` | `check` | `check`, `install`, or `latest` |
| `pve_microcode_package` | `""` | Specific .deb filename for `install` action |
| `pve_microcode_auto_reboot` | `false` | Reboot after installation |
| `pve_microcode_vendor` | `""` | Override auto-detection (`intel` or `amd`) |

## Tags

| Tag | Description |
|-----|-------------|
| `microcode` | Install + reboot — use this for mixed Intel/AMD environments |
| `install` | Install only, no reboot |
| `intel` | Intel tasks only |
| `amd` | AMD tasks only |
| `reboot` | Reboot only (if auto_reboot enabled) |

## Examples

```bash
# Check status
ansible-playbook playbooks/pve/microcode.yml

# Install latest on all hosts
ansible-playbook playbooks/pve/microcode.yml --tags microcode

# Verify after reboot
journalctl -k | grep -E "microcode" | head -n 1
```
