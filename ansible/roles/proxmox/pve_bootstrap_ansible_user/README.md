# pve_bootstrap_ansible_user

Creates a dedicated ansible user on Proxmox hosts with SSH key auth and passwordless sudo.

## Usage

Run once as root to bootstrap hosts:

```bash
ansible-playbook playbooks/pve/bootstrap.yml -u root
```

After running, update inventory to use `ansible_user: ansible`.

## Actions

- Creates `ansible` user
- Installs sudo if required
- Adds SSH key from GitHub
- Configures passwordless sudo
- Verifies sudo access

## Variables

```yaml
ansible_user_name: ansible
ansible_user_groups: [sudo]
ansible_ssh_github_user: "monstermuffin"
ansible_ssh_public_key: "https://github.com/{{ ansible_ssh_github_user }}.keys"
```
