# podman
Installs Podman and configures system-wide registries and the systemd Quadlet directory.

## Rootful vs Rootless

**Rootful** (default): Don't set `podman_user`. Configs go to `/etc/containers/`, Quadlets to `/etc/containers/systemd/`.

**Rootless**: Set `podman_user` and the role will create the app user. Quadlets will be placed in `~/.config/containers/systemd/` and systemd lingering will be enabled for that user.
