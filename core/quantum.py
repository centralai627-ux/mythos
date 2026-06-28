"""
Mythos Quantum Techniques
========================
Quantum-inspired algorithms untuk optimasi dan perhitungan.
Bukan quantum computing beneran, tapi teknik yang terinspirasi dari prinsip quantum.
"""
from __future__ import annotations
import math
import random
import hashlib
from typing import List, Callable, Any, Tuple


def quantum_annealing_optimize(
    cost_function: Callable,
    initial_state: Any,
    iterations: int = 1000,
    temperature: float = 1.0,
    cooling_rate: float = 0.99
) -> Any:
    """
    Quantum-inspired simulated annealing untuk optimasi.
    Berguna untuk: scheduling, resource allocation, routing.
    """
    current_state = initial_state
    current_cost = cost_function(current_state)
    best_state = current_state
    best_cost = current_cost

    for i in range(iterations):
        # Generate neighbor state
        neighbor = _perturb_state(current_state)
        neighbor_cost = cost_function(neighbor)

        # Accept or reject
        delta = neighbor_cost - current_cost
        if delta < 0 or random.random() < math.exp(-delta / max(temperature, 0.01)):
            current_state = neighbor
            current_cost = neighbor_cost

            if current_cost < best_cost:
                best_state = current_state
                best_cost = current_cost

        temperature *= cooling_rate

    return best_state


def _perturb_state(state: Any) -> Any:
    """Generate a slightly different state."""
    if isinstance(state, list):
        new_state = state.copy()
        if len(new_state) > 0:
            idx = random.randint(0, len(new_state) - 1)
            new_state[idx] = random.choice(new_state)
        return new_state
    elif isinstance(state, dict):
        new_state = state.copy()
        if new_state:
            key = random.choice(list(new_state.keys()))
            if isinstance(new_state[key], (int, float)):
                new_state[key] += random.uniform(-1, 1)
        return new_state
    return state


def grover_search(data: List[Any], target: Any) -> int:
    """
    Grover's search algorithm simulation.
    Mencari item dalam list secara efisien.
    Berguna untuk: search dalam knowledge base.
    """
    n = len(data)
    if n == 0:
        return -1

    # Quantum-inspired search with speedup
    iterations = int(math.sqrt(n)) + 1

    for _ in range(iterations):
        # Random amplitude amplification
        idx = random.randint(0, n - 1)
        if data[idx] == target:
            return idx

    # Fallback to linear search
    for i, item in enumerate(data):
        if item == target:
            return i

    return -1


def quantum_walk_search(graph: dict, start: Any, target: Any, max_steps: int = 100) -> Any:
    """
    Quantum walk search untuk graph traversal.
    Berguna untuk: navigasi knowledge graph, dependency resolution.
    """
    current = start
    visited = set()

    for step in range(max_steps):
        if current == target:
            return current

        visited.add(current)
        neighbors = graph.get(current, [])

        if not neighbors:
            break

        # Quantum-inspired probabilistic selection
        unvisited = [n for n in neighbors if n not in visited]
        if not unvisited:
            break

        # Weighted random selection (amplitude amplification)
        current = random.choice(unvisited)

    return None


def quantum_correlation_search(data: List[dict], query: dict) -> List[dict]:
    """
    Quantum-inspired correlation search untuk knowledge base.
    Berguna untuk: RAG, similarity search.
    """
    results = []

    for item in data:
        score = 0
        for key, value in query.items():
            if key in item:
                if isinstance(value, str) and isinstance(item[key], str):
                    # String similarity
                    score += _string_similarity(value.lower(), item[key].lower())
                elif value == item[key]:
                    score += 1.0

        if score > 0:
            results.append({**item, '_score': score})

    # Sort by score (quantum amplitude ordering)
    results.sort(key=lambda x: x['_score'], reverse=True)
    return results


def _string_similarity(s1: str, s2: str) -> float:
    """Calculate string similarity using common substring matching."""
    if not s1 or not s2:
        return 0.0

    # Simple Jaccard similarity on words
    words1 = set(s1.split())
    words2 = set(s2.split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def quantum_sort(data: List[Any], key: Callable = None) -> List[Any]:
    """
    Quantum-inspired sorting using parallel comparison.
    Berguna untuk: sorting large datasets.
    """
    if len(data) <= 1:
        return data

    # Quantum-inspired parallel merge sort
    if len(data) <= 10:
        return sorted(data, key=key) if key else sorted(data)

    # Split and conquer
    mid = len(data) // 2
    left = quantum_sort(data[:mid], key)
    right = quantum_sort(data[mid:], key)

    return _merge(left, right, key)


def _merge(left: List, right: List, key: Callable = None) -> List:
    """Merge two sorted lists."""
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        left_val = key(left[i]) if key else left[i]
        right_val = key(right[j]) if key else right[j]

        if left_val <= right_val:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


def quantum_probability_distribution(outcomes: List[str], weights: List[float]) -> dict:
    """
    Quantum probability distribution untuk predicted outcomes.
    Berguna untuk: risk assessment, prediction, decision making.
    """
    total = sum(weights)
    if total == 0:
        return {o: 1.0 / len(outcomes) for o in outcomes}

    distribution = {}
    for outcome, weight in zip(outcomes, weights):
        distribution[outcome] = weight / total

    return distribution


def quantum_entanglement_score(features_a: List[float], features_b: List[float]) -> float:
    """
    Quantum entanglement score untuk correlation analysis.
    Berguna untuk: feature correlation, pattern detection.
    """
    if len(features_a) != len(features_b) or len(features_a) == 0:
        return 0.0

    # Calculate correlation coefficient (quantum-inspired)
    n = len(features_a)
    mean_a = sum(features_a) / n
    mean_b = sum(features_b) / n

    numerator = sum((a - mean_a) * (b - mean_b) for a, b in zip(features_a, features_b))
    denom_a = sum((a - mean_a) ** 2 for a in features_a) ** 0.5
    denom_b = sum((b - mean_b) ** 2 for b in features_b) ** 0.5

    if denom_a * denom_b == 0:
        return 0.0

    return numerator / (denom_a * denom_b)


# === Tool Interface ===
def quantum_tool(query: str) -> str:
    """
    Tool interface untuk quantum calculations.
    Dipanggil oleh AI untuk perhitungan quantum.
    """
    query_lower = query.lower()

    if 'optimize' in query_lower or 'optimasi' in query_lower:
        return (
            "Quantum Optimization available:\n"
            "- quantum_annealing_optimize: Untuk optimasi scheduling, routing\n"
            "- quantum_sort: Sorting efisien\n"
            "- quantum_correlation_search: Pencarian korelasi"
        )

    if 'search' in query_lower or 'cari' in query_lower:
        return (
            "Quantum Search available:\n"
            "- grover_search: Pencarian cepat dalam list\n"
            "- quantum_walk_search: Graph traversal\n"
            "- quantum_correlation_search: Pencarian korelasi"
        )

    if 'probability' in query_lower or 'probabilitas' in query_lower:
        return (
            "Quantum Probability available:\n"
            "- quantum_probability_distribution: Distribusi probabilitas\n"
            "- quantum_entanglement_score: Analisis korelasi fitur"
        )

    return (
        "Quantum Techniques available:\n"
        "1. Optimization: quantum_annealing_optimize, quantum_sort\n"
        "2. Search: grover_search, quantum_walk_search\n"
        "3. Analysis: quantum_correlation_search, quantum_probability_distribution\n"
        "4. Correlation: quantum_entanglement_score\n\n"
        "Usage: Ask AI to use quantum techniques for specific tasks."
    )


# === NEW QUANTUM TECHNIQUES ===

def quantum_neural_network(inputs: List[float], weights: List[List[float]], activation: str = 'sigmoid') -> List[float]:
    """
    Quantum Neural Network simulation.
    Berguna untuk: pattern recognition, classification, prediction.
    
    Args:
        inputs: Input features
        weights: Network weights (2D array)
        activation: Activation function (sigmoid, relu, tanh)
    
    Returns:
        Output neurons
    """
    def sigmoid(x):
        return 1 / (1 + math.exp(-max(-500, min(500, x))))
    
    def relu(x):
        return max(0, x)
    
    def tanh(x):
        return math.tanh(x)
    
    act_fn = {'sigmoid': sigmoid, 'relu': relu, 'tanh': tanh}.get(activation, sigmoid)
    
    current = inputs
    for layer_weights in weights:
        new_layer = []
        for neuron_weights in layer_weights:
            # Quantum-inspired weighted sum with noise
            weighted_sum = sum(w * i for w, i in zip(neuron_weights, current))
            # Add small quantum noise
            weighted_sum += random.gauss(0, 0.01)
            new_layer.append(act_fn(weighted_sum))
        current = new_layer
    
    return current


def quantum_cluster(data: List[List[float]], n_clusters: int = 3, iterations: int = 100) -> List[int]:
    """
    Quantum-inspired K-means clustering.
    Berguna untuk: categorization, grouping similar items.
    
    Args:
        data: List of feature vectors
        n_clusters: Number of clusters
        iterations: Max iterations
    
    Returns:
        Cluster assignments for each data point
    """
    if not data or n_clusters <= 0:
        return []
    
    n = len(data)
    if n <= n_clusters:
        return list(range(n))
    
    # Initialize centroids randomly
    centroids = random.sample(data, min(n_clusters, n))
    
    assignments = [0] * n
    
    for _ in range(iterations):
        # Assign points to nearest centroid
        for i, point in enumerate(data):
            min_dist = float('inf')
            min_cluster = 0
            for j, centroid in enumerate(centroids):
                dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(point, centroid)))
                if dist < min_dist:
                    min_dist = dist
                    min_cluster = j
            assignments[i] = min_cluster
        
        # Update centroids
        new_centroids = []
        for k in range(n_clusters):
            cluster_points = [data[i] for i in range(n) if assignments[i] == k]
            if cluster_points:
                # Quantum-inspired weighted average
                centroid = [sum(p[j] for p in cluster_points) / len(cluster_points) 
                           for j in range(len(cluster_points[0]))]
                new_centroids.append(centroid)
            else:
                new_centroids.append(centroids[k])
        
        centroids = new_centroids
    
    return assignments


def quantum_pathfind(graph: dict, start: Any, end: Any) -> Tuple[List[Any], float]:
    """
    Quantum-inspired Dijkstra pathfinding.
    Berguna untuk: navigation, dependency resolution, routing.
    
    Args:
        graph: Adjacency dict {node: [(neighbor, weight), ...]}
        start: Start node
        end: End node
    
    Returns:
        (path, total_weight)
    """
    import heapq
    
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous = {node: None for node in graph}
    visited = set()
    
    # Priority queue: (distance, node)
    pq = [(0, start)]
    
    while pq:
        current_dist, current = heapq.heappop(pq)
        
        if current in visited:
            continue
        visited.add(current)
        
        if current == end:
            # Reconstruct path
            path = []
            while current is not None:
                path.append(current)
                current = previous[current]
            return path[::-1], distances[end]
        
        for neighbor, weight in graph.get(current, []):
            if neighbor not in visited:
                new_dist = current_dist + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
    
    return [], float('inf')  # No path found


def quantum_encrypt(data: str, key: str) -> str:
    """
    Quantum-inspired encryption.
    Berguna untuk: data protection, secure storage.
    
    Args:
        data: Plain text
        key: Encryption key
    
    Returns:
        Encrypted string (hex)
    """
    # Quantum-inspired XOR cipher with key derivation
    key_hash = hashlib.md5(key.encode()).hexdigest()
    
    encrypted = []
    for i, char in enumerate(data):
        # Quantum-inspired: combine character with key at position
        key_byte = ord(key_hash[i % len(key_hash)])
        char_byte = ord(char)
        # XOR with quantum noise
        encrypted_byte = char_byte ^ key_byte ^ (i % 256)
        encrypted.append(format(encrypted_byte, '02x'))
    
    return ''.join(encrypted)


def quantum_decrypt(encrypted: str, key: str) -> str:
    """
    Quantum-inspired decryption.
    Berguna untuk: data recovery, secure storage.
    
    Args:
        encrypted: Encrypted string (hex)
        key: Encryption key
    
    Returns:
        Decrypted string
    """
    key_hash = hashlib.md5(key.encode()).hexdigest()
    
    decrypted = []
    for i in range(0, len(encrypted), 2):
        hex_byte = encrypted[i:i+2]
        if len(hex_byte) < 2:
            break
        encrypted_byte = int(hex_byte, 16)
        key_byte = ord(key_hash[(i // 2) % len(key_hash)])
        char_byte = encrypted_byte ^ key_byte ^ ((i // 2) % 256)
        decrypted.append(chr(char_byte))
    
    return ''.join(decrypted)


def quantum_recommend(user_preferences: dict, item_features: List[dict], top_n: int = 5) -> List[dict]:
    """
    Quantum-inspired recommendation system.
    Berguna untuk: content recommendation, suggestion.
    
    Args:
        user_preferences: User preference vector
        item_features: List of item feature dicts
        top_n: Number of recommendations
    
    Returns:
        Top N recommended items with scores
    """
    scored_items = []
    
    for item in item_features:
        score = 0
        for key, pref_value in user_preferences.items():
            if key in item:
                item_value = item[key]
                if isinstance(pref_value, (int, float)) and isinstance(item_value, (int, float)):
                    # Quantum-inspired similarity
                    score += 1.0 / (1.0 + abs(pref_value - item_value))
                elif pref_value == item_value:
                    score += 1.0
        
        scored_items.append({**item, '_score': score})
    
    scored_items.sort(key=lambda x: x['_score'], reverse=True)
    return scored_items[:top_n]


def quantum_anomaly_detection(data: List[float], threshold: float = 2.0) -> List[int]:
    """
    Quantum-inspired anomaly detection.
    Berguna untuk: error detection, outlier detection.
    
    Args:
        data: List of values
        threshold: Standard deviations for anomaly
    
    Returns:
        List of anomaly indices
    """
    if len(data) < 3:
        return []
    
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std = math.sqrt(variance)
    
    anomalies = []
    for i, value in enumerate(data):
        z_score = abs(value - mean) / std if std > 0 else 0
        if z_score > threshold:
            anomalies.append(i)
    
    return anomalies


def quantum_time_series_forecast(data: List[float], steps: int = 5) -> List[float]:
    """
    Quantum-inspired time series forecasting.
    Berguna untuk: prediction, trend analysis.
    
    Args:
        data: Historical data points
        steps: Number of steps to forecast
    
    Returns:
        Forecasted values
    """
    if len(data) < 2:
        return data * steps
    
    # Calculate trend
    n = len(data)
    x_mean = (n - 1) / 2
    y_mean = sum(data) / n
    
    numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(data))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    
    slope = numerator / denominator if denominator > 0 else 0
    intercept = y_mean - slope * x_mean
    
    # Generate forecast with quantum noise
    forecast = []
    for i in range(steps):
        predicted = intercept + slope * (n + i)
        # Add quantum noise
        noise = random.gauss(0, abs(predicted) * 0.05)
        forecast.append(predicted + noise)
    
    return forecast


def quantum_feature_importance(features: List[str], data: List[dict], target: str) -> List[dict]:
    """
    Quantum-inspired feature importance analysis.
    Berguna untuk: feature selection, model interpretation.
    
    Args:
        features: List of feature names
        data: List of data points with features
        target: Target variable name
    
    Returns:
        Feature importance scores sorted by importance
    """
    importances = {}
    
    for feature in features:
        # Calculate correlation with target
        values = [item.get(feature, 0) for item in data]
        targets = [item.get(target, 0) for item in data]
        
        if not values or not targets:
            importances[feature] = 0
            continue
        
        # Quantum-inspired correlation
        n = len(values)
        mean_v = sum(values) / n
        mean_t = sum(targets) / n
        
        numerator = sum((v - mean_v) * (t - mean_t) for v, t in zip(values, targets))
        denom_v = sum((v - mean_v) ** 2 for v in values) ** 0.5
        denom_t = sum((t - mean_t) ** 2 for t in targets) ** 0.5
        
        correlation = numerator / (denom_v * denom_t) if denom_v * denom_t > 0 else 0
        importances[feature] = abs(correlation)
    
    # Sort by importance
    result = [{'feature': f, 'importance': imp} for f, imp in importances.items()]
    result.sort(key=lambda x: x['importance'], reverse=True)
    
    return result
