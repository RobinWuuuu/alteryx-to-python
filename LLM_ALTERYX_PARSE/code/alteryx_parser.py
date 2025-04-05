import xml.etree.ElementTree as ET
import pandas as pd
import re


def load_alteryx_nodes(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    rows = []

    def inner_xml(element):
        # Join the XML string of all child elements.
        return ''.join(ET.tostring(child, encoding='unicode') for child in element)

    def traverse(node):
        if node.tag == 'Node':
            tool_id = node.attrib.get("ToolID")
            if tool_id:
                gui_settings = node.find("GuiSettings")
                tool_type = gui_settings.attrib.get("Plugin") if gui_settings is not None else None
                if tool_type:
                    # Extract the last component from the dotted string.
                    clear_name = tool_type.split('.')[-1]
                    # Remove trailing parentheses if present.
                    if clear_name.endswith("()"):
                        clear_name = clear_name[:-2]
                    # Convert to title case for clarity.
                    tool_type = clear_name.title()
                text = inner_xml(node)
                rows.append([tool_id, tool_type, text])
        # Recursively traverse child nodes.
        for child in node:
            traverse(child)

    traverse(root)
    df_nodes = pd.DataFrame(rows, columns=["tool_id", "tool_type", "text"])


    return df_nodes


def load_alteryx_connections(file_path):
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    connections = []

    # Locate the <Connections> element in the XML file.
    connections_element = root.find("Connections")
    if connections_element is not None:
        # Iterate over each <Connection> element
        for connection in connections_element.findall("Connection"):
            origin = connection.find("Origin")
            destination = connection.find("Destination")
            if origin is not None and destination is not None:
                connections.append({
                    "origin_tool_id": origin.attrib.get("ToolID"),
                    "origin_connection": origin.attrib.get("Connection"),
                    "destination_tool_id": destination.attrib.get("ToolID"),
                    "destination_connection": destination.attrib.get("Connection")
                })

    # Create a DataFrame from the list of connections.
    return pd.DataFrame(connections)


def load_alteryx_data(file_path):
    try:
        df_nodes = load_alteryx_nodes(file_path)
        df_connections = load_alteryx_connections(file_path)
        return df_nodes, df_connections
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        return pd.DataFrame(), pd.DataFrame()  # Return empty DataFrames on error
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame(), pd.DataFrame()  # Return empty DataFrames on error


def extract_container_children(df_nodes):
    """
    For each container row in df_nodes (where tool_type is 'ToolContainer'),
    search the text for occurrences of ToolID numbers, remove the container's own ID,
    and return a DataFrame with columns:
       - container_id: the container's ToolID
       - child_tools: a list of child ToolID strings found in the text.
    """
    results = []

    # Filter container rows using a case-insensitive check
    container_rows = df_nodes[df_nodes["tool_type"].str.lower() == "toolcontainer"]

    if container_rows.empty:
        print("No ToolContainer found in df_nodes.")  # Debugging information

    for _, row in container_rows.iterrows():
        container_id = row["tool_id"]
        container_text = row["text"]
        # Find all occurrences of ToolID="some_number"
        found_ids = re.findall(r'ToolID="(\d+)"', container_text)
        # Remove the container's own id from the list (if present)
        child_ids = [tid for tid in found_ids if tid != container_id]
        results.append({
            "container_id": container_id,
            "child_tools": child_ids
        })

    return pd.DataFrame(results, columns=["container_id", "child_tools"])


def clean_container_children(df_containers, df_nodes):
    """
    Given a DataFrame of container children (with columns 'container_id' and 'child_tools')
    and the original df_nodes, remove any child tool whose tool_type is either "Toolcontainer" or "BrowseV2".
    Returns a new DataFrame with the cleaned child_tools.
    """
    cleaned_results = []

    for _, row in df_containers.iterrows():
        container_id = row["container_id"]
        child_ids = row["child_tools"]
        filtered_ids = []
        for cid in child_ids:
            # Look up the child tool in df_nodes by its ToolID.
            matching = df_nodes[df_nodes["tool_id"] == cid]
            if not matching.empty:
                # Check the tool type (case-insensitive)
                child_type = matching.iloc[0]["tool_type"]
                if child_type not in {"Toolcontainer", "BrowseV2"}:
                    filtered_ids.append(cid)
            else:
                # If the child tool isn't found, include it (or you can choose to exclude it)
                filtered_ids.append(cid)

        cleaned_results.append({
            "container_id": container_id,
            "child_tools": filtered_ids
        })

    return pd.DataFrame(cleaned_results, columns=["container_id", "child_tools"])