# pve_bootstrap_ansible_user

Creates a dedicated ansible user on Proxmox hosts with SSH key auth and passwordless sudo.
It does not create a separate admin user.

## Usage

Run once as root to bootstrap hosts:

```bash
ansible-playbook playbooks/pve/bootstrap.yml -u root
```

## Variables

```yaml
ansible_user_name: ansible
ansible_user_groups: [sudo]
ansible_authorized_keys: |
  ssh-ed25519 AAAA... ansible_new
  ssh-ed25519 AAAA... muffin@mbp.internal.muffn.io
```
