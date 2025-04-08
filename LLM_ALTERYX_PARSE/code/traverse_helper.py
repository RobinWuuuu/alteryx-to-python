from collections import defaultdict
import pandas as pd
import networkx as nx


def get_execution_order(df_nodes, df_connections):
    """
    Returns a list of tool_ids in execution order based on the connections.
    It builds a directed graph using origin and destination tool IDs from df_connections,
    then performs a topological sort.
    """
    G = nx.DiGraph()

    # Add all nodes (tool IDs) from df_nodes
    for tool_id in df_nodes["tool_id"]:
        G.add_node(tool_id)

    # Add edges: each edge from an origin tool to a destination tool
    for _, row in df_connections.iterrows():
        origin = row["origin_tool_id"]
        destination = row["destination_tool_id"]
        if pd.notnull(origin) and pd.notnull(destination):
            G.add_edge(origin, destination)

    try:
        # Get a topological sort of the graph, which reflects the execution order
        execution_order = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        raise Exception("Cycle detected in workflow connections!")

    return execution_order


def adjust_order(random_tool_ids, execution_sequence):
    # Build a lookup dictionary mapping tool IDs to their position.
    sequence_lookup = {tool: index for index, tool in enumerate(execution_sequence)}
    return sorted(random_tool_ids, key=lambda tool: sequence_lookup.get(tool, float('inf')))


def parse_linear_chains(df_connections):
    """
    Parse all linear chains from a connections DataFrame.

    A 'linear chain' is a sequence of nodes where each node
    (except possibly the first and last) has exactly one in_degree and one out_degree.
    Branching (out_degree > 1) or convergence (in_degree > 1) cause the chain to split.

    Parameters:
        df_connections (pd.DataFrame): Must have columns:
            'origin_tool_id' and 'destination_tool_id'.

    Returns:
        list of lists: Each inner list is a chain of node IDs in linear order.
    """
    # 1) Build adjacency list and track in/out degrees.
    adj_list = defaultdict(list)
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)

    # Collect all unique nodes to handle isolated cases if necessary
    all_nodes = set(df_connections["origin_tool_id"]) | set(df_connections["destination_tool_id"])

    # Build graph
    for _, row in df_connections.iterrows():
        u = str(row["origin_tool_id"])
        v = str(row["destination_tool_id"])
        adj_list[u].append(v)
        out_degree[u] += 1
        in_degree[v] += 1

    # Ensure every node is represented in the dictionaries
    for node in all_nodes:
        adj_list[node] = adj_list[node]  # just to ensure a key is present
        in_degree[node] = in_degree[node]
        out_degree[node] = out_degree[node]

    # 2) Keep track of which edges are "used"
    used_edges = set()  # store as tuples (u, v)

    # Helper function to build a single chain starting from edge (u -> v)
    def build_chain(u, v):
        chain = [u, v]
        used_edges.add((u, v))
        current = v

        # Follow the chain while the current node is "linear": in_degree=1, out_degree=1
        while in_degree[current] == 1 and out_degree[current] == 1:
            # current has exactly one neighbor in adj_list
            next_nodes = adj_list[current]
            if not next_nodes:
                break
            nxt = next_nodes[0]  # only child
            # Mark edge as used
            if (current, nxt) in used_edges:
                break
            chain.append(nxt)
            used_edges.add((current, nxt))
            current = nxt

        return chain

    # 3) Main loop: for each node u, for each neighbor v, if edge (u, v) not used => build a chain
    chains = []
    for u in adj_list:
        for v in adj_list[u]:
            if (u, v) not in used_edges:
                chain = build_chain(u, v)
                chains.append(chain)

    return chains


def get_tools_without_input(df_connections):
    """
    Identify tools that do not have any input connections.

    Parameters:
        df_connections (pd.DataFrame): DataFrame containing columns 'origin_tool_id' and 'destination_tool_id'.

    Returns:
        list: A list of tool IDs that never appear as a destination (i.e., have no input).
    """
    origin_tools = set(df_connections["origin_tool_id"])
    destination_tools = set(df_connections["destination_tool_id"])
    tools_without_input = origin_tools - destination_tools
    return list(tools_without_input)


def get_next_tools(df_connections, tool_id):
    # Filter the rows where the given tool_id is the origin
    next_tools = df_connections[df_connections["origin_tool_id"] == tool_id]["destination_tool_id"].unique().tolist()
    next_tools_count = len(next_tools)
    return next_tools


def get_previous_tools(df_connections, tool_id):
    # Filter the rows where the given tool_id is the destination
    previous_tools = df_connections[df_connections["destination_tool_id"] == tool_id]["origin_tool_id"].unique().tolist()
    previous_tools_count = len(previous_tools)
    return previous_tools, previous_tools_count


def get_output_name(df_connections, tool_id):
    # Filter rows where the given tool_id is the origin
    filtered = df_connections[df_connections["origin_tool_id"] == tool_id]

    if filtered.empty:
        return []

    # Get unique origin connection types
    output_types = filtered["origin_connection"].unique()

    # Format each output type with the tool_id
    output_names = [f"df_{tool_id}_{conn_type}" for conn_type in output_types]
    return output_names


def get_input_name(df_connections, tool_id):
    # Filter rows where the given tool_id is the destination
    filtered = df_connections[df_connections["destination_tool_id"] == tool_id]

    results = []
    for _, row in filtered.iterrows():
        input_df_name = f"df_{row['origin_tool_id']}_{row['origin_connection']}"
        input_type = row["destination_connection"]
        results.append([input_df_name, input_type])

    return results





