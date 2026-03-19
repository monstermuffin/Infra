# Group-Based Permissions Setup

## 1. Create Groups in Pocket ID

1. Go to **Groups** in Pocket ID admin
2. Create a group — the **Groups Claim Name** (e.g. `proxmox_admins`) is what matters, not the display name
3. Add users to the group

## 2. Configure OIDC Client in Pocket ID

- Ensure "groups" scope is enabled
- Add your groups to "Allowed User Groups"

## 3. Update Ansible Config

In `inventory/group_vars/proxmox.yml`:

```yaml
pve_pocketid_sync_groups: true
pve_pocketid_autocreate_groups: true
pve_pocketid_manage_groups: true

# Proxmox appends the realm suffix to OIDC groups:
# proxmox_admins -> proxmox_admins-pocketid
pve_pocketid_groups:
  - name: "proxmox_admins-pocketid"
    comment: "Administrators from Pocket ID"
    acl:
      - path: "/"
        role: "Administrator"
        propagate: true
```

## 4. Run

```bash
ansible-playbook playbooks/pve/pocketid_realm.yml
```

## How It Works

1. User logs in via Pocket ID
2. OIDC token includes `groups: ["proxmox_admins"]`
3. Proxmox syncs and creates local group `proxmox_admins-pocketid`
4. ACLs on that group grant the user permissions automatically
