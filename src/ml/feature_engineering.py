import math
import collections

def compute_entropy(text: str) -> float:
    """Calculate the Shannon entropy of a string."""
    if not text:
        return 0.0
    frequencies = collections.Counter(text)
    length = len(text)
    entropy = -sum((freq / length) * math.log2(freq / length) for freq in frequencies.values())
    return entropy

def extract_url_features(url: str):
    """Extract application-layer features from a URL."""
    length = len(url)
    entropy = compute_entropy(url)
    return length, entropy

def combine_features(url_length, url_entropy, qber_mean, qber_variance, qber_crossings):
    """
    Fuses application logic (URL features) with channel physics (QBER).
    Expected by the QSVM. Length 5 feature vector.
    """
    return [url_length, url_entropy, qber_mean, qber_variance, qber_crossings]
