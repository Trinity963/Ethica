import pytest
from unittest.mock import patch, MagicMock
import matplotlib.pyplot as plt

def mock_packet_counts():
    return {
        'TCP': 150,
        'UDP': 80,
        'ICMP': 20,
        'Other': 5
    }

@patch("matplotlib.pyplot.bar")
@patch("matplotlib.pyplot.show")
def test_render_packet_distribution(mock_show, mock_bar):
    data = mock_packet_counts()

    # Simulate a render function
    def render_packet_graph(data):
        protocols = list(data.keys())
        counts = list(data.values())

        plt.figure(figsize=(8, 4))
        plt.bar(protocols, counts, color='skyblue')
        plt.title("Network Packet Distribution")
        plt.xlabel("Protocol")
        plt.ylabel("Count")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    render_packet_graph(data)

    # Assert matplotlib was called
    assert mock_bar.called
    assert mock_show.called