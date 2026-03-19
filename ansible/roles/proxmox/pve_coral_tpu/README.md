1) we will do the# pve_coral_tpu

Install Google Coral USB TPU Edge runtime on Proxmox VE hosts.

## Variables

- `pve_coral_enabled` - Enable installation (must be set per host)
- `pve_coral_runtime_version` - Runtime version: "std" (cooler) or "max" (default, faster but hot)
- `pve_coral_install_pycoral` - Install Python PyCoral library for testing
- `pve_coral_verify_install` - Verify TPU device detection after install
- `pve_coral_create_udev_rule` - Create `/dev/coral-tpu` symlink for LXC passthrough (default: true)

## Usage

```bash
ansible-playbook playbooks/pve/coral_tpu.yml --limit pve01.lcy.muffn.io
```

## Important Notes

**Device Initialization**: The Coral USB starts as `1a6e:089a Global Unichip Corp.` and changes to `18d1:9302 Google Inc.` after first use. This is normal and expected behavior. The device will initialize automatically when first accessed by an application (e.g., Frigate, TensorFlow Lite).

**After installation**: Unplug and replug the USB device for udev rules to take effect. The device will show as "Global Unichip Corp." until an application uses it for the first time.

## LXC Passthrough

For LXC containers, this role creates a udev rule that provides a stable device node at `/dev/coral-tpu`. Unlike QEMU VMs, **LXC containers do not support USB passthrough via `usb0`, `usb1` parameters**. Instead, pass through the character device:

```yaml
frigate_devices:
  - type: "device"
    path: "/dev/coral-tpu"
    gid: 46  # plugdev group
```

The udev rule handles both device states (before/after initialization) automatically.
