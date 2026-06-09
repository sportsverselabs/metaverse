"""DNS / website agent — connects sportsversusnews.com to the VPS. Guidance + verification only.

Generates the exact DNS records to add in Hostinger, and can verify resolution/SSL once live.
It makes no changes itself — the owner adds DNS records in the Hostinger panel.
"""

from __future__ import annotations

import socket
from typing import Optional

from core.logging_setup import get_logger

DOMAIN = "sportsversusnews.com"


class DnsWebsiteAgent:
    name = "dns_website_agent"

    def __init__(self, domain: str = DOMAIN, logger=None) -> None:
        self.domain = domain
        self.log = logger or get_logger("agent.dns_website")

    def required_records(self, vps_ip: str = "<VPS_IP>") -> list:
        return [
            {"type": "A", "host": "@", "value": vps_ip, "ttl": 3600, "note": "root domain -> VPS"},
            {"type": "A", "host": "www", "value": vps_ip, "ttl": 3600, "note": "www -> VPS"},
            {"type": "A", "host": "dashboard", "value": vps_ip, "ttl": 3600, "note": "owner dashboard subdomain"},
        ]

    def instructions(self, vps_ip: str = "<VPS_IP>") -> str:
        recs = self.required_records(vps_ip)
        lines = [f"Point {self.domain} at your Hostinger VPS:",
                 "1. Hostinger panel -> Domains -> DNS / Nameservers.",
                 "2. Add/replace these records:"]
        for r in recs:
            lines.append(f"   {r['type']:<5} {r['host']:<10} -> {r['value']}  (TTL {r['ttl']})  # {r['note']}")
        lines.append("3. Wait for propagation (minutes to a few hours).")
        lines.append("4. On the VPS, set up SSL (certbot) once DNS resolves.")
        lines.append("I need: your Hostinger VPS IP address to fill in the records.")
        return "\n".join(lines)

    def verify(self, host: Optional[str] = None) -> dict:
        """Best-effort DNS resolution check (no external API)."""
        target = host or self.domain
        try:
            ip = socket.gethostbyname(target)
            return {"domain": target, "resolves": True, "ip": ip}
        except (socket.gaierror, OSError):
            return {"domain": target, "resolves": False, "ip": None}
