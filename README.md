# Infrastructure v2

v1 was a mess and could not be uploaded publically without many breaking changes, was also created at a time when I was learning and so this contributed to the mess.


This repo is a rewrite of my infrastructure, starting from scratch with many changes to the tools and technologies used.

## Git-Crypt

Data deemed 'sensitive', such as reconnaissance data, app domain names, etc, stay in dedicated `bindings.yml` inventory files. These files are managed via `git-crypt`.

Example files will be provided with example data for reference.

## TODO

- [ ] Understand Claude's solution to lxc selection.
- [ ] Fix/Understand why `netavark` is accumulating stale nftables DNAT rules when `state: restarted` is used, or any kind of redeploy happens.
  - Current 'workaround' is rebooting the LXC.
