from pyvis.network import Network
import networkx as nx
import os
import numpy as np

def create_network_graph(activities_dependencies, total_float_results, file_path):
    G = nx.DiGraph()

    # Add nodes to the graph
    for activity in activities_dependencies:
        tooltip = f'{activity}: Appeared {total_float_results.get(activity, 0)} times as critical'
        G.add_node(activity, title=tooltip)

    # Add edges based on dependencies with weights reflecting criticality
    for activity, dependencies in activities_dependencies.items():
        for dep in dependencies:
            weight = total_float_results.get(activity, 0)
            G.add_edge(dep, activity, weight=weight)

    nt = Network(directed=True)
    nt.from_nx(G)

    html_content = nt.generate_html()

    with open(file_path, 'w') as file:
        file.write(html_content)
