# pve_kernel_clean

Removes old PVE kernel packages. Never touches the running kernel.

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `pve_kernel_clean_action` | `list` | `list`, `clean` (keep N), or `clean-all` |
| `pve_kernel_clean_keep_versions` | `1` | Old versions to keep when using `clean` |
| `pve_kernel_clean_autoremove` | `true` | Run apt autoremove after |
| `pve_kernel_clean_update_grub` | `true` | Update GRUB after |

## Tags

| Tag | Description |
|-----|-------------|
| `clean` | Remove old kernels (respects keep_versions) |
| `clean-all` | Remove all old kernels |
| `autoremove` | apt autoremove only |
| `grub` | Update GRUB only |

## Examples

```bash
# See what's installed (default action is list)
ansible-playbook playbooks/pve/kernel_clean.yml

# Remove old kernels
ansible-playbook playbooks/pve/kernel_clean.yml --tags clean

# Remove all old kernels
ansible-playbook playbooks/pve/kernel_clean.yml --tags clean-all
```
