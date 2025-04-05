#!/usr/bin/env python
"""
main.py

A simple Streamlit-based UI to convert an Alteryx workflow (.yxmd) to Python code.

Features:
  - Browse for an Alteryx workflow file.
  - Enter an OpenAI API key.
  - Input a comma-separated list of tool IDs.
  - Run conversion to generate Python code.
  - Display the final Python script.
  - Debug logging to trace execution.

Usage:
    streamlit run main.py
"""

import os
import sys
import streamlit as st
import logging
from pathlib import Path

# Configure debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)


def set_project_root(marker: str = "README.md"):
    """
    Walk up parent directories until the marker file is found.
    Once found, set that directory as the working directory and add it to sys.path.
    """
    current_dir = Path().resolve()
    logging.debug(f"Starting search for project root from: {current_dir}")
    for parent in [current_dir, *current_dir.parents]:
        if (parent / marker).exists():
            os.chdir(parent)
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            st.write(f"Working directory set to: {os.getcwd()}")
            return
    raise FileNotFoundError(f"Marker '{marker}' not found in any parent directory of {current_dir}")


# Uncomment below if you want to set the project root automatically.
# set_project_root()

# -- Import project modules (adjust paths as needed) --
try:
    from code import alteryx_parser as parser
    from code import prompt_helper

    st.write("Project modules imported successfully.")
    logging.debug("Project modules imported successfully.")
except Exception as e:
    st.error("Error importing project modules.")
    st.exception(e)
    logging.exception("Error importing project modules.")
    st.stop()

st.title("Alteryx to Python Converter")

# File uploader: user browses for a .yxmd file.
uploaded_file = st.sidebar.file_uploader("Select Alteryx Workflow File", type=["yxmd"])

# Input for the OpenAI API key.
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Input for the tool IDs (comma separated).
tool_ids_input = st.text_input("Tool IDs (comma separated)", placeholder="e.g., 644, 645, 646")


container_tool_id = st.sidebar.text_input("Enter Container Tool ID")
if st.sidebar.button("Fetch Child Tool IDs"):

    # Save the uploaded file to a temporary path.
    temp_file_path = "uploaded_workflow.yxmd"
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.write(f"File saved to {temp_file_path}.")
    logging.debug(f"File saved to {temp_file_path}.")
    
    # Check if the uploaded file is valid
    if temp_file_path is not None:
        # Load the Alteryx data from the uploaded file
        df_nodes, df_connections = parser.load_alteryx_data(temp_file_path)
        st.sidebar.write(df_nodes.shape)
        
        # Display child tool IDs if a container tool ID is provided
        if container_tool_id:
            # Extract container children
            df_containers = parser.extract_container_children(df_nodes)
            st.sidebar.write(df_containers.shape)
            df_containers = parser.clean_container_children(df_containers, df_nodes)
            
            # Find the specific container
            container_info = df_containers[df_containers["container_id"] == container_tool_id]
            if not container_info.empty:
                # Convert child tool IDs to a string like list
                child_tool_ids = list(container_info["child_tools"].values[0])
                child_tool_ids_string = f"[{', '.join(map(str, child_tool_ids))}]"
                st.sidebar.write("Child Tool IDs:", child_tool_ids_string)
            else:
                st.sidebar.write("No child tools found for this Container Tool ID.")
    else:
        st.sidebar.write("Please upload a valid Alteryx Workflow file.")

if st.button("Run Conversion"):
    # Basic input validation.
    if not uploaded_file or not api_key or not tool_ids_input:
        st.error("Please provide all required inputs.")
        logging.error("Missing one or more required inputs.")
    else:
        # Save the uploaded file to a temporary path.
        temp_file_path = "uploaded_workflow.yxmd"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.write(f"File saved to {temp_file_path}.")
        logging.debug(f"File saved to {temp_file_path}.")

        # Clean up tool IDs input: remove double quotes and split by comma.
        tool_ids_clean = tool_ids_input.replace('"', '').replace("'", '').replace("[", '').replace("]", '')
        tool_ids = [tid.strip() for tid in tool_ids_clean.split(",") if tid.strip()]
        st.write(f"Parsed tool IDs: {tool_ids}")
        logging.debug(f"Parsed tool IDs: {tool_ids}")

        # Set the OpenAI API key as an environment variable.
        os.environ["OPENAI_API_KEY"] = api_key
        logging.debug("OPENAI_API_KEY set in environment.")

        try:
            # Load Alteryx nodes and connections from the selected file.
            df_nodes, df_connections = parser.load_alteryx_data(temp_file_path)
            st.write(f"Loaded {len(df_nodes)} nodes and {len(df_connections)} connections.")
            logging.debug(f"Loaded {len(df_nodes)} nodes and {len(df_connections)} connections.")

            # Filter out unwanted tool types.
            df_nodes = df_nodes[~df_nodes["tool_type"].isin(["BrowseV2", "Toolcontainer"])]
            st.write(f"After filtering, {len(df_nodes)} nodes remain.")
            logging.debug(f"After filtering, {len(df_nodes)} nodes remain.")
            print(tool_ids)
            # Generate Python code for the specified tool IDs.
            test_df = df_nodes.loc[df_nodes["tool_id"].isin(tool_ids)]
            st.write(f"Generating code for {len(test_df)} tool(s)...")
            logging.debug(f"Generating code for {len(test_df)} tool(s) with tool IDs: {tool_ids}")
            df_generated_code = prompt_helper.generate_python_code_from_alteryx_df(test_df, df_connections)
            logging.debug("Generated code DataFrame columns: " + str(df_generated_code.columns.tolist()))
            st.write("Generated code DataFrame columns:", df_generated_code.columns.tolist())

            # Fix: If "tool_id" is missing in df_generated_code, add it from test_df.
            if "tool_id" not in df_generated_code.columns:
                st.write("Adding missing 'tool_id' column to generated code DataFrame.")
                logging.debug("Adding missing 'tool_id' column to generated code DataFrame.")
                df_generated_code.insert(0, "tool_id", test_df["tool_id"].values)

            # Combine code snippets for the specified tools.
            final_script = prompt_helper.combine_python_code_of_tools(tool_ids, df_generated_code)
            st.success("Conversion succeeded!")
            logging.debug("Final script generated successfully.")
            st.code(final_script, language="python")
        except Exception as e:
            st.error("Conversion Error:")
            st.exception(e)
            logging.exception("Error during conversion process.")
