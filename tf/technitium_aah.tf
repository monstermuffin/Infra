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
}
