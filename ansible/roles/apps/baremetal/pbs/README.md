# pbs

Installs PBS 4, in this case under a Trixie LXC.

1. Adds the PBS Trixie no-subscription APT repository
2. Disables the PBS enterprise repository
3. Installs the minimal `proxmox-backup-server` package set
4. Enables and starts the PBS daemons
5. Bootstraps an `admin@pbs` user so the GUI is usable without a host PAM password


```bash
ansible-playbook playbooks/lxc/deploy_pbs.yml
ansible-playbook playbooks/lxc/deploy_pbs.yml --tags repo
ansible-playbook playbooks/lxc/deploy_pbs.yml --tags auth < updates the auth if requried, should work after the fact
```

Should support older PBS releases? idk. Why use old when new?
```yaml
pbs_repo_suite: bookworm
pbs_keyring_url: https://enterprise.proxmox.com/debian/proxmox-release-bookworm.gpg
```

WebUI: `https://<host>:8007`.

## Auth Bootstrap

PBS does not need the PDM-style file hack. The supported approach is to create a `pbs`
realm user through `proxmox-backup-manager` and grant it an ACL on `/`.

```bash
proxmox-backup-manager user create admin@pbs --password '...'
proxmox-backup-manager acl update / Admin --auth-id admin@pbs
```
