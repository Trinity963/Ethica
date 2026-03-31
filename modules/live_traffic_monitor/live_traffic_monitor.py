import logging
import requests
from scapy.all import sniff, IP
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO, format='[LiveTrafficMonitor] %(message)s')
logger = logging.getLogger(__name__)

class LiveTrafficMonitor:
    """
    Monitors live network traffic using scapy, tracks packet sources, and flags anomalies.
    Optionally fetches geolocation data via external API.
    """

    def __init__(self, geolocate=True):
        """
        Initialize the LiveTrafficMonitor class.

        Args:
            geolocate (bool): Whether to fetch geolocation data for IP addresses.
        """
        self.packet_count = Counter()
        self.geolocate = geolocate

    def get_geolocation(self, ip):
        """
        Fetch geolocation for a given IP address using ip-api.com.

        Args:
            ip (str): IP address to look up.

        Returns:
            str: Location string "City, Country" or "Unknown, Unknown".
        """
        if not self.geolocate:
            return "Geolocation disabled"

        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
            if response.status_code == 200:
                data = response.json()
                city = data.get("city", "Unknown")
                country = data.get("country", "Unknown")
                return f"{city}, {country}"
        except Exception as e:
            logger.warning(f"Error fetching geolocation for {ip}: {e}")
        return "Unknown, Unknown"

    def packet_callback(self, packet):
        """
        Callback function to process each captured IP packet.

        Args:
            packet: scapy packet object.
        """
        if IP in packet:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            location = self.get_geolocation(src_ip)
            logger.info(f"Packet from {src_ip} ({location}) to {dst_ip}")
            self.packet_count[src_ip] += 1

    def detect_anomalies(self, threshold=100):
        """
        Analyze captured data and flag high-volume IPs.

        Args:
            threshold (int): Volume threshold to flag anomalies.
        """
        logger.info("Detecting anomalies...")
        for ip, count in self.packet_count.items():
            if count > threshold:
                logger.warning(f"Anomaly detected: {ip} sent {count} packets.")

    def start_monitoring(self, duration=30):
        """
        Start sniffing packets for a specified duration.

        Args:
            duration (int): Time in seconds to monitor traffic.
        """
        logger.info(f"Starting live traffic monitoring for {duration} seconds...")
        sniff(prn=self.packet_callback, store=False, timeout=duration)
        logger.info("Monitoring complete.")
        self.detect_anomalies()

# Example usage
if __name__ == "__main__":
    monitor = LiveTrafficMonitor(geolocate=False)
    monitor.start_monitoring(duration=15)