# pve_pocketid_realm

Configures a Pocket ID OIDC authentication realm on Proxmox VE hosts with optional group-based permission assignment.

## Usage

Set credentials in `inventory/group_vars/proxmox.yml`:

```yaml
pve_pocketid_issuer_url: "https://auth.muffn.io"
pve_pocketid_client_id: "proxmox-cluster"
pve_pocketid_client_secret: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  ...
```

Enable per-host in `inventory/host_vars/pve01.yml`:

```yaml
pve_pocketid_enabled: true
```

Run:

```bash
ansible-playbook playbooks/pve/pocketid_realm.yml
ansible-playbook playbooks/pve/pocketid_realm.yml --tags info
ansible-playbook playbooks/pve/pocketid_realm.yml --tags remove
```

## Group Sync

Proxmox appends the realm ID as a suffix to OIDC groups. If Pocket ID sends `proxmox_admins` and your realm ID is `pocketid`, Proxmox creates `proxmox_admins-pocketid`. Use the **suffixed name** in your config:

```yaml
pve_pocketid_groups:
  - name: "proxmox_admins-pocketid"
    comment: "Full admin access from Pocket ID"
    acl:
      - path: "/"
        role: "Administrator"
        propagate: true
```

## Tags

| Tag | Description |
|-----|-------------|
| `info`, `status` | Show current realm status |
| `configure`, `setup`, `present` | Create/update realm and groups |
| `groups`, `permissions` | Manage groups and ACLs only |
| `remove`, `absent`, `revert` | Remove realm |

## Callback URLs

Configure these wildcards in your Pocket ID client:

```
https://10.83.2.*:8006   (AAH)
https://10.82.2.*:8006   (LCY)
https://10.84.2.*:8006   (LGW)
https://pve*.*.muffn.io  (all hosts by FQDN)
```

## Troubleshooting

```bash
pveum realm list
pveum group list
pveum acl list
pveum user permissions youruser@pocketid
cat /etc/pve/domains.cfg
```
