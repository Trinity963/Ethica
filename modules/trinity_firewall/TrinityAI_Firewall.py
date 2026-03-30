#!/usr/bin/env python3
# TrinityAI OS - AI-Driven Firewall & Intrusion Prevention System
# Reborn for /mnt/TrinityAI integration

import json
import logging
import os
import threading
import socket
import scapy.all as scapy

# Configure logging in sacred path
log_dir = "/mnt/TrinityAI/security/firewall/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "firewall.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load policies from sacred config
def load_firewall_policies():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", "firewall_policies.json"), "r") as f:
        return json.load(f)

class FirewallModule:
    def __init__(self):
        self.policies = load_firewall_policies()

    def packet_callback(self, packet):
        if packet.haslayer(scapy.IP):
            src_ip = packet[scapy.IP].src
            dst_ip = packet[scapy.IP].dst
            logging.info(f"Packet Captured - Source: {src_ip} -> Destination: {dst_ip}")
            for rule in self.policies["blocked_ips"]:
                if src_ip == rule or dst_ip == rule:
                    logging.warning(f"Blocked Suspicious Traffic: {src_ip} -> {dst_ip}")
                    return False
        return True

    def start_intrusion_detection(self):
        scapy.sniff(prn=self.packet_callback, store=False)

class PortScannerModule:
    def __init__(self, host="0.0.0.0"):
        self.host = host

    def detect_port_scans(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        for port in range(1, 65535):
            result = sock.connect_ex((self.host, port))
            if result == 0:
                logging.warning(f"Port scan detected on port {port}")
        sock.close()

def start_firewall():
    logging.info("🔥 TrinityAI Firewall & IPS Activated.")
    firewall = FirewallModule()
    firewall_thread = threading.Thread(target=firewall.start_intrusion_detection)
    firewall_thread.daemon = True
    firewall_thread.start()
    logging.info("👁️ Intrusion Detection System Running.")

if __name__ == "__main__":
    start_firewall()
