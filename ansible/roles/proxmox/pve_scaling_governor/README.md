# pve_scaling_governor

Manage CPU frequency scaling governor on Proxmox VE.

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `pve_scaling_governor` | `""` | Governor to set (`performance`, `powersave`, `schedutil`, etc). Empty = display only |
| `pve_scaling_governor_persistent` | `false` | Persist across reboots via crontab `@reboot` |
| `pve_scaling_governor_remove_persistence` | `false` | Remove existing crontab persistence |

## Tags

| Tag | Description |
|-----|-------------|
| `set` | Set the scaling governor |
| `persistence` | Manage crontab persistence |
| `remove` | Remove crontab persistence |

## Usage

```bash
# Check current governor
ansible-playbook playbooks/pve/scaling_governor.yml

# Set governor
ansible-playbook playbooks/pve/scaling_governor.yml --tags set

# Set up persistence
ansible-playbook playbooks/pve/scaling_governor.yml --tags persistence
```

## Notes

- Applied to all CPU cores simultaneously
- Without persistence, settings revert on reboot
- Persistence uses crontab `@reboot` with 60s delay for cpufreq init
- Modern kernels default to `schedutil`
