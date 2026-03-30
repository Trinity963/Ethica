import pytest
from unittest.mock import patch, MagicMock
from live_traffic_monitor import LiveTrafficMonitor

def test_monitor_init_defaults():
    monitor = LiveTrafficMonitor()
    assert monitor.geolocate is False
    assert isinstance(monitor.packet_counts, dict)

@patch("live_traffic_monitor.sniff")
def test_monitor_sniffing(mock_sniff):
    # Setup
    mock_sniff.return_value = []
    monitor = LiveTrafficMonitor()
    monitor.start_monitoring(duration=1)

    # Check that sniff was called
    mock_sniff.assert_called_once()
    assert isinstance(monitor.packet_counts, dict)

def test_geolocation_toggle():
    # Geolocation should be off by default
    monitor = LiveTrafficMonitor()
    assert not monitor.geolocate

    # Geolocation enabled
    monitor_geo = LiveTrafficMonitor(geolocate=True)
    assert monitor_geo.geolocate