#!/usr/bin/env python
"""
main.py

A simple Streamlit-based UI to convert an Alteryx workflow (.yxmd) to Python code.

Features:
  - Browse for an Alteryx workflow file.
  - Enter an OpenAI API key.
  - (Optional) Fetch child tool IDs by specifying a container tool ID.
  - Input a comma-separated list of tool IDs you want to convert.
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

    logging.debug("Project modules imported successfully.")
except Exception as e:
    st.error("Error importing project modules.")
    st.exception(e)
    logging.exception("Error importing project modules.")
    st.stop()

st.title("Alteryx to Python Converter")

# Short instructions for the user
st.markdown(
    """
**How to Use this App**  
1. **Upload a .yxmd file** in the sidebar.  
2. **Enter your OpenAI API Key** (required for code generation).  
3. (Optional) **Enter a Container Tool ID** and click "Fetch Child Tool IDs" to get child tools for that container.  
4. **Provide your Tool IDs** in the main text box (comma-separated).  
5. **Click "Run Conversion"** to generate Python code.
""",
    unsafe_allow_html=True
)

# File uploader: user browses for a .yxmd file.
uploaded_file = st.sidebar.file_uploader("Select Alteryx Workflow File", type=["yxmd"])

# Input for the OpenAI API key.
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Container instructions
st.sidebar.markdown("_If you have a container tool in your workflow, you can fetch its child tool IDs here:_")

# Input for the container tool ID
container_tool_id = st.sidebar.text_input("Enter Container Tool ID")

# Button to fetch child tool IDs
if st.sidebar.button("Fetch Child Tool IDs"):
    if not uploaded_file:
        st.sidebar.warning("Please upload a .yxmd file before fetching child IDs.")
    else:
        # Save the uploaded file to a temporary path.
        temp_file_path = "uploaded_workflow.yxmd"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        logging.debug(f"File saved to {temp_file_path} for container child ID lookup.")

        # Load Alteryx data
        df_nodes, df_connections = parser.load_alteryx_data(temp_file_path)

        # If the user provided a container tool ID
        if container_tool_id:
            df_containers = parser.extract_container_children(df_nodes)
            df_containers = parser.clean_container_children(df_containers, df_nodes)

            # Find the specific container
            container_info = df_containers[df_containers["container_id"] == container_tool_id]
            if not container_info.empty:
                child_tool_ids = list(container_info["child_tools"].values[0])
                child_tool_ids_string = f"[{', '.join(map(str, child_tool_ids))}]"
                st.sidebar.write("**Child Tool IDs:**", child_tool_ids_string)
            else:
                st.sidebar.write("No child tools found for this Container Tool ID.")

# Input for the tool IDs (comma separated).
tool_ids_input = st.text_input(
    "Tool IDs (comma separated)",
    placeholder="e.g., 644, 645, 646",
    help=("Enter one or more tool IDs separated by commas. For example: '644, 645, 646'. "
          "It's recommended to group tools that are logically connected together. "
          "Note: Each tool takes about 4 seconds to generate, so parsing 10 tools may take around 40 seconds.")
)

extra_user_instructions = st.text_input(
    "Extra User Instruction (optional)",
    placeholder="e.g., These tools help clean the CD data.",
    help="You can provide additional instructions for the code generation."
)

# Button to run the conversion
if st.button("Run Conversion"):
    # Basic input validation
    if not uploaded_file or not api_key or not tool_ids_input:
        st.error("Please upload a .yxmd file, provide an API key, and enter tool IDs.")
        logging.error("Missing one or more required inputs.")
    else:
        # Save the uploaded file to a temporary path.
        temp_file_path = "uploaded_workflow.yxmd"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        logging.debug(f"File saved to {temp_file_path} for conversion.")

        # Clean up tool IDs input: remove double quotes/brackets and split by comma.
        tool_ids_clean = tool_ids_input.replace('"', '').replace("'", '').replace("[", '').replace("]", '')
        tool_ids = [tid.strip() for tid in tool_ids_clean.split(",") if tid.strip()]
        logging.debug(f"Parsed tool IDs: {tool_ids}")

        # Set the OpenAI API key as an environment variable.
        os.environ["OPENAI_API_KEY"] = api_key
        logging.debug("OPENAI_API_KEY set in environment.")


        try:
            # Display a message placeholder and a progress bar.
            message_placeholder = st.empty()
            progress_bar = st.progress(0)

            # Load Alteryx nodes and connections from the selected file.
            message_placeholder.write("Parse alteryx file...")
            df_nodes, df_connections = parser.load_alteryx_data(temp_file_path)
            logging.debug(f"Loaded {len(df_nodes)} nodes and {len(df_connections)} connections.")
            progress_bar.progress(5)

            # Filter out unwanted tool types.
            df_nodes = df_nodes[~df_nodes["tool_type"].isin(["BrowseV2", "Toolcontainer"])]
            logging.debug(f"After filtering, {len(df_nodes)} nodes remain.")

            # Generate Python code for the specified tool IDs.
            test_df = df_nodes.loc[df_nodes["tool_id"].isin(tool_ids)]
            message_placeholder.write(f"**Generating code for {len(test_df)} tool(s), it may take {len(test_df)*4} seconds...**")
            logging.debug(f"Generating code for {len(test_df)} tool(s) with tool IDs: {tool_ids}")


            df_generated_code = prompt_helper.generate_python_code_from_alteryx_df(test_df, df_connections, progress_bar)

            # If "tool_id" is missing in df_generated_code, insert it
            if "tool_id" not in df_generated_code.columns:
                logging.debug("Adding missing 'tool_id' column to generated code DataFrame.")
                df_generated_code.insert(0, "tool_id", test_df["tool_id"].values)

            message_placeholder.write("**Working on combining code snippets...**")

            # Combine code snippets for the specified tools.
            final_script = prompt_helper.combine_python_code_of_tools(tool_ids, df_generated_code, extra_user_instructions = extra_user_instructions)
            message_placeholder.write("**Finished generating code!**")
            progress_bar.progress(100)
            st.success("Conversion succeeded! Scroll down to see your Python code.")
            st.code(final_script, language="python")
        except Exception as e:
            st.error("Conversion Error:")
            st.exception(e)
            logging.exception("Error during conversion process.")
