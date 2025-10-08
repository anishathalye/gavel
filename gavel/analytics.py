"""
Advanced analytics for CrowdBT algorithm performance and network analysis.
"""
from gavel.models import Item, Decision, Annotator
import networkx as nx
from collections import defaultdict
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import func


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
        # Only add edges if both winner and loser are in the graph (i.e., both are active)
        if dec.winner.id in G.nodes and dec.loser.id in G.nodes:
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


# ========================================
# 3. PROJECT COVERAGE HEATMAP
# ========================================

def get_coverage_matrix():
    """
    Generate a comparison coverage matrix showing which project pairs have been compared.
    Returns a matrix where cell (i,j) shows how many times project i was compared to project j.
    """
    items = Item.query.filter(Item.active == True).order_by(Item.id).all()
    decisions = Decision.query.all()

    # Create project ID to index mapping
    project_ids = [item.id for item in items]
    id_to_idx = {pid: idx for idx, pid in enumerate(project_ids)}

    # Initialize matrix
    n = len(project_ids)
    matrix = [[0 for _ in range(n)] for _ in range(n)]

    # Fill matrix with comparison counts
    for dec in decisions:
        winner_idx = id_to_idx.get(dec.winner_id)
        loser_idx = id_to_idx.get(dec.loser_id)

        if winner_idx is not None and loser_idx is not None:
            matrix[winner_idx][loser_idx] += 1
            matrix[loser_idx][winner_idx] += 1  # Symmetric

    # Calculate coverage statistics
    total_possible_comparisons = n * (n - 1) // 2
    actual_comparisons = sum(1 for i in range(n) for j in range(i+1, n) if matrix[i][j] > 0)
    coverage_percentage = (actual_comparisons / total_possible_comparisons * 100) if total_possible_comparisons > 0 else 0

    # Find under-compared pairs
    avg_comparisons_per_pair = sum(matrix[i][j] for i in range(n) for j in range(i+1, n)) / total_possible_comparisons if total_possible_comparisons > 0 else 0

    under_compared_pairs = []
    for i in range(n):
        for j in range(i+1, n):
            if matrix[i][j] < avg_comparisons_per_pair * 0.5:  # Less than 50% of average
                under_compared_pairs.append({
                    'project_a': items[i].name,
                    'project_b': items[j].name,
                    'comparisons': matrix[i][j]
                })

    return {
        'matrix': matrix,
        'project_ids': project_ids,
        'project_names': [item.name for item in items],
        'coverage_percentage': coverage_percentage,
        'avg_comparisons_per_pair': avg_comparisons_per_pair,
        'under_compared_pairs': under_compared_pairs[:10]  # Top 10
    }


# ========================================
# 4. VOTING ACTIVITY TIMELINE
# ========================================

def get_voting_timeline(hours=2):
    """
    Get voting activity over time.
    Returns vote counts in 15-second buckets for the last N hours.
    """
    from gavel import db

    decisions = Decision.query.order_by(Decision.time).all()

    if not decisions:
        return {
            'timeline_data': [],
            'total_votes': 0,
            'votes_last_minute': 0,
            'peak_time': None,
            'avg_votes_per_minute': 0
        }

    # Get time range
    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours)

    # Filter decisions in time range
    recent_decisions = [d for d in decisions if d.time >= start_time]

    # Create 15-second buckets
    bucket_counts = defaultdict(int)
    for dec in recent_decisions:
        # Round down to nearest 15 seconds
        bucket_time = dec.time.replace(microsecond=0)
        second = (bucket_time.second // 15) * 15
        bucket_time = bucket_time.replace(second=second)
        bucket_counts[bucket_time] += 1

    # Fill in missing buckets with 0
    timeline_data = []
    current = start_time.replace(microsecond=0)
    current = current.replace(second=(current.second // 15) * 15)

    while current <= now:
        count = bucket_counts.get(current, 0)
        timeline_data.append({
            'time': current.isoformat(),
            'timestamp': int(current.timestamp() * 1000),  # milliseconds for JS
            'display_time': current.strftime('%H:%M:%S'),
            'count': count
        })
        current += timedelta(seconds=15)

    # Calculate statistics
    total_votes = len(decisions)

    # Votes in last minute (4 buckets of 15 seconds)
    votes_last_minute = sum(bucket_counts.get(now.replace(microsecond=0).replace(second=(now.second // 15) * 15) - timedelta(seconds=15*i), 0) for i in range(4))

    peak_bucket = max(timeline_data, key=lambda x: x['count']) if timeline_data else None
    peak_time = peak_bucket['display_time'] if peak_bucket else None

    # Average votes per minute
    total_minutes = hours * 60
    avg_votes_per_minute = len(recent_decisions) / total_minutes if total_minutes > 0 else 0

    return {
        'timeline_data': timeline_data,
        'total_votes': total_votes,
        'votes_last_minute': votes_last_minute,
        'peak_time': peak_time,
        'avg_votes_per_minute': avg_votes_per_minute
    }


# ========================================
# 7. STATISTICAL SUMMARY DASHBOARD
# ========================================

def get_statistical_summary():
    """
    Calculate comprehensive statistical summary for dashboard.
    """
    from gavel import crowd_bt

    items = Item.query.filter(Item.active == True).all()
    judges = Annotator.query.all()
    decisions = Decision.query.all()

    if not items or not decisions:
        return {
            'total_comparisons': 0,
            'total_projects': len(items),
            'total_judges': len(judges),
            'avg_comparisons_per_project': 0,
            'avg_comparisons_per_judge': 0,
            'completion_percentage': 0,
            'convergence_status': 'Not Started',
            'avg_uncertainty': 0,
            'estimated_votes_needed': 0
        }

    # Basic counts
    total_comparisons = len(decisions)
    total_projects = len(items)
    total_judges = len(judges)
    active_judges = len([j for j in judges if j.active])

    # Comparisons per project
    project_comparison_counts = defaultdict(int)
    for dec in decisions:
        project_comparison_counts[dec.winner_id] += 1
        project_comparison_counts[dec.loser_id] += 1

    avg_comparisons_per_project = sum(project_comparison_counts.values()) / (2 * total_projects) if total_projects > 0 else 0

    # Comparisons per judge
    judge_comparison_counts = defaultdict(int)
    for dec in decisions:
        judge_comparison_counts[dec.annotator_id] += 1

    avg_comparisons_per_judge = total_comparisons / total_judges if total_judges > 0 else 0

    # Completion percentage (based on minimum comparisons needed)
    # Assume we want at least 10 comparisons per project
    min_comparisons_needed = total_projects * 10
    completion_percentage = min(100, (total_comparisons / min_comparisons_needed * 100)) if min_comparisons_needed > 0 else 0

    # Convergence analysis
    avg_uncertainty = sum(float(item.sigma_sq) for item in items) / len(items)
    initial_sigma_sq = float(crowd_bt.SIGMA_SQ_PRIOR)

    if avg_uncertainty < 0.5:
        convergence_status = 'Converged'
    elif avg_uncertainty < 1.0:
        convergence_status = 'Nearly Converged'
    elif avg_uncertainty < initial_sigma_sq * 0.8:
        convergence_status = 'In Progress'
    else:
        convergence_status = 'Early Stage'

    # Estimate votes needed
    estimated_votes_needed = estimate_votes_to_convergence(target_avg_sigma_sq=0.5)

    # Projects with high uncertainty
    high_uncertainty_projects = sorted(
        [(item.name, float(item.sigma_sq)) for item in items],
        key=lambda x: x[1],
        reverse=True
    )[:5]

    return {
        'total_comparisons': total_comparisons,
        'total_projects': total_projects,
        'total_judges': total_judges,
        'active_judges': active_judges,
        'avg_comparisons_per_project': round(avg_comparisons_per_project, 1),
        'avg_comparisons_per_judge': round(avg_comparisons_per_judge, 1),
        'completion_percentage': round(completion_percentage, 1),
        'convergence_status': convergence_status,
        'avg_uncertainty': round(avg_uncertainty, 3),
        'estimated_votes_needed': estimated_votes_needed if estimated_votes_needed else 0,
        'high_uncertainty_projects': high_uncertainty_projects
    }
