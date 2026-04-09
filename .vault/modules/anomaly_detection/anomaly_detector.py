import logging
from sklearn.ensemble import IsolationForest
import numpy as np

class AnomalyDetector:
    """
    A simple anomaly detector using the Isolation Forest algorithm.
    Useful for detecting unusual patterns in network traffic or behavior data.
    """

    def __init__(self, contamination=0.1):
        """
        Initialize the anomaly detector.

        Args:
            contamination (float): The proportion of outliers in the data set.
        """
        self.model = IsolationForest(contamination=contamination)

    def train_model(self, training_data):
        """
        Train the anomaly detection model on the provided data.

        Args:
            training_data (np.ndarray): A 2D array of training samples.
        """
        logging.info("[AnomalyDetector] Training model...")
        self.model.fit(training_data)

    def predict_anomalies(self, new_data):
        """
        Predict anomalies in new data samples.

        Args:
            new_data (np.ndarray): A 2D array of new samples to evaluate.

        Returns:
            np.ndarray: An array with values 1 (normal) and -1 (anomaly).
        """
        logging.info("[AnomalyDetector] Predicting anomalies...")
        return self.model.predict(new_data)

# Example usage
if __name__ == "__main__":
    detector = AnomalyDetector()
    training_data = np.array([[100], [200], [300], [400], [500]])  # Normal traffic patterns
    detector.train_model(training_data)

    new_data = np.array([[100], [200], [300], [5000], [6000]])  # New traffic with outliers
    anomalies = detector.predict_anomalies(new_data)
    logging.info("Anomalies detected: %s", anomalies)