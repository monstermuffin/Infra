# ---------------------------------------------------------------------------
# Technitium DNS — AAH (technitium{xx}.aah.muffn.io)
#
# Manages the aah.muffn.io zone and all host records for the AAH cluster.
#
# LXC records are populated at deploy time by ops/gen_lxc_dns.py for this site.
#
# ---------------------------------------------------------------------------
# TODO: Conditionals not supported?

resource "technitium_server_settings" "aah" {
  provider = technitium.aah

  recursion             = "AllowOnlyForPrivateNetworks"
  recursion_network_acl = ["10.0.0.0/8", "127.0.0.0/8"]
  dnssec_validation     = true
  qname_minimization    = true
  randomize_name        = true
  log_queries           = true
  enable_blocking       = false
  forwarders            = ["9.9.9.9:853", "149.112.112.112:853"]
  forwarder_protocol    = "Tls"
  serve_stale           = true
}

resource "technitium_zone" "aah" {
  provider = technitium.aah

  name                   = "aah.muffn.io"
  type                   = "Primary"
  soa_serial_date_scheme = true
}

# PVE nodes are not LXCs so the generator does not pick them up.
locals {
  aah_infra_records = {
    "pve02.aah.muffn.io" = {
      ip  = "10.82.2.152"
      ttl = 3600
    }
    "pve03.aah.muffn.io" = {
      ip  = "10.82.2.153"
      ttl = 3600
    }
    "pve04.aah.muffn.io" = {
      ip  = "10.82.2.154"
      ttl = 3600
    }
  }

  aah_lxc_records = {
    for r in var.lxc_dns_records : "${r.name}.${r.zone}" => {
      ip  = r.ip
      ttl = 300
    } if r.zone == technitium_zone.aah.name
  }

  aah_vm_records = {
    for fqdn, record in local.proxmox_vm_dns_records : fqdn => {
      ip  = record.ip
      ttl = 300
    } if record.zone == technitium_zone.aah.name
  }

  aah_host_records = merge(
    local.aah_infra_records,
    local.aah_lxc_records,
    local.aah_vm_records,
  )

  aah_reverse_records = {
    for fqdn, record in local.aah_host_records : fqdn => {
      ip  = record.ip
      ttl = record.ttl
      zone = format(
        "%s.%s.%s.in-addr.arpa",
        split(".", record.ip)[2],
        split(".", record.ip)[1],
        split(".", record.ip)[0],
      )
      name = format(
        "%s.%s.%s.%s.in-addr.arpa",
        split(".", record.ip)[3],
        split(".", record.ip)[2],
        split(".", record.ip)[1],
        split(".", record.ip)[0],
      )
    }
  }

  aah_reverse_zones = toset([
    for record in values(local.aah_reverse_records) : record.zone
  ])
}

resource "technitium_record" "aah_infra" {
  for_each = local.aah_infra_records
  provider = technitium.aah

  zone  = technitium_zone.aah.name
  name  = each.key
  type  = "A"
  value = each.value.ip
  ttl   = each.value.ttl
}

resource "technitium_record" "aah_lxc_hosts" {
  for_each = local.aah_lxc_records
  provider = technitium.aah

  zone  = technitium_zone.aah.name
  name  = each.key
  type  = "A"
  value = each.value.ip
  ttl   = each.value.ttl

  depends_on = [technitium_zone.aah]
}

resource "technitium_record" "aah_vm_hosts" {
  for_each = local.aah_vm_records
  provider = technitium.aah

  zone  = technitium_zone.aah.name
  name  = each.key
  type  = "A"
  value = each.value.ip
  ttl   = each.value.ttl

  depends_on = [technitium_zone.aah]
}

resource "technitium_zone" "aah_reverse" {
  for_each = local.aah_reverse_zones
  provider = technitium.aah

  name                   = each.value
  type                   = "Primary"
  soa_serial_date_scheme = true
}

resource "technitium_record" "aah_ptr" {
  for_each = local.aah_reverse_records
  provider = technitium.aah

  zone  = each.value.zone
  name  = each.value.name
  type  = "PTR"
  value = each.key
  ttl   = each.value.ttl

  depends_on = [technitium_zone.aah_reverse]
}
