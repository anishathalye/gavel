"""
Advanced analytics for CrowdBT algorithm performance and network analysis.
"""
from gavel.models import Item, Decision
import networkx as nx
from collections import defaultdict
import numpy as np


def build_comparison_graph():
    """
    Build a directed graph where nodes are projects and edges are comparisons.
    Edge weight represents number of times A was preferred over B.
    """
    G = nx.DiGraph()

    # Add all active projects as nodes
    items = Item.query.filter(Item.active == True).all()
    for item in items:
        G.add_node(item.id, name=item.name, mu=float(item.mu), sigma_sq=float(item.sigma_sq))

    # Add edges from decisions
    decisions = Decision.query.all()
    edge_weights = defaultdict(int)

    for dec in decisions:
        # Directed edge from winner to loser
        edge = (dec.winner.id, dec.loser.id)
        edge_weights[edge] += 1

    for (winner_id, loser_id), weight in edge_weights.items():
        G.add_edge(winner_id, loser_id, weight=weight)

    return G


def estimate_votes_to_convergence(target_avg_sigma_sq=0.1):
    """
    Estimate how many more votes needed for rankings to stabilize.
    Uses historical rate of uncertainty reduction.
    """
    from gavel import crowd_bt

    items = Item.query.filter(Item.active == True).all()
    decisions = Decision.query.all()

    if not items or not decisions:
        return None

    current_avg_sigma_sq = sum(float(item.sigma_sq) for item in items) / len(items)

    if current_avg_sigma_sq <= target_avg_sigma_sq:
        return 0

    total_votes = len(decisions)
    initial_sigma_sq = float(crowd_bt.SIGMA_SQ_PRIOR)

    if total_votes == 0 or current_avg_sigma_sq >= initial_sigma_sq:
        # Can't estimate, use pessimistic estimate
        remaining = current_avg_sigma_sq - target_avg_sigma_sq
        # Assume each vote reduces by 0.01 on average
        return int(remaining / 0.01)

    # Decay rate: sigma_sq(t) = sigma_sq(0) * exp(-k*t)
    # k = ln(sigma_sq(0) / sigma_sq(t)) / t
    decay_rate = np.log(initial_sigma_sq / current_avg_sigma_sq) / total_votes

    # Solve for t when sigma_sq(t) = target
    # t = ln(sigma_sq(0) / target) / k
    votes_to_target = int(np.log(initial_sigma_sq / target_avg_sigma_sq) / decay_rate)

    remaining_votes = max(0, votes_to_target - total_votes)

    return remaining_votes


def generate_graph_data_for_visualization(G):
    """
    Generate JSON-serializable data for D3.js force-directed graph.
    """
    nodes = []
    links = []

    # Create nodes
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        nodes.append({
            'id': str(node_id),
            'name': node_data['name'],
            'mu': node_data['mu'],
            'sigma_sq': node_data['sigma_sq'],
            'size': 5 + (node_data['mu'] + 3) * 2  # Scale by mu for visual sizing
        })

    # Create links
    for source, target in G.edges():
        weight = G[source][target].get('weight', 1)
        links.append({
            'source': str(source),
            'target': str(target),
            'weight': weight,
            'value': weight  # D3 uses 'value' for link strength
        })

    return {'nodes': nodes, 'links': links}
