# Infrastructure v2

v1 was a mess and could not be uploaded publically without many breaking changes, was also created at a time when I was learning and so this contributed to the mess.


This repo is a rewrite of my infrastructure, starting from scratch with many changes to the tools and technologies used.

## Git-Crypt

Data deemed 'sensitive', such as reconnaissance data, app domain names, etc, stay in dedicated `bindings.yml` inventory files. These files are managed via `git-crypt`.

Example files will be provided with example data for reference.

## TODO

- [X] Understand Claude's solution to lxc selection.
- [ ] Deploy tf config for full VM deployment and management.
- [ ] Find / Write a tf provider that has full functionality for Proxmox LXC containers.
- [ ] Tweak Removate config to ensure automerge is doing its thing correctly.
- [ ] Fix/Understand why `netavark` is accumulating stale nftables DNAT rules when `state: restarted` is used, or any kind of redeploy happens.
  - Current 'workaround' is rebooting the LXC.
