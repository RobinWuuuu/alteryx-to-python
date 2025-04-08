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
    from code import traverse_helper

    logging.debug("Project modules imported successfully.")
except Exception as e:
    st.error("Error importing project modules.")
    st.exception(e)
    logging.exception("Error importing project modules.")
    st.stop()

# --------------------- Sidebar ---------------------------
# --------------------- Sidebar ---------------------------
# --------------------- Sidebar ---------------------------
st.sidebar.header("Step 1 - Upload Workflow File")
# File uploader: user browses for a .yxmd file.
uploaded_file = st.sidebar.file_uploader("Select Alteryx Workflow File", type=["yxmd"])
st.sidebar.header("Step 2 - Upload OpenAI API Key")

# Input for the OpenAI API key.
api_key = st.sidebar.text_input("OpenAI API Key", type="password")


st.sidebar.markdown("---")
st.sidebar.header("Helpers")

st.sidebar.header("Helper 1 - Get Execution Sequence")
# Sidebar: Button to generate the execution sequence

# Initialize session state for sequence generation if not already set
if "sequence_generated" not in st.session_state:
    st.session_state.sequence_generated = False
if "sequence_str" not in st.session_state:
    st.session_state.sequence_str = ""

if st.sidebar.button("Generate Sequence"):
    if not uploaded_file:
        st.sidebar.warning("Please upload a .yxmd file before generating the execution sequence.")
    else:
        # Save the uploaded file to a temporary path
        temp_file_path = "uploaded_workflow.yxmd"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        logging.debug(f"File saved to {temp_file_path} for generating execution sequence.")

        # Load Alteryx data
        df_nodes, df_connections = parser.load_alteryx_data(temp_file_path)

        # Generate execution sequence (list of tool IDs)
        execution_sequence = traverse_helper.get_execution_order(df_nodes, df_connections)
        st.session_state.sequence_str = ", ".join(str(tid) for tid in execution_sequence)

        # Mark sequence as generated in session state
        st.session_state.sequence_generated = True

# If a sequence was generated, display the persistent message and download button
if st.session_state.sequence_generated:
    st.sidebar.write("Execution sequence of current file has been generated.")
    st.sidebar.download_button(
        label="Download Sequence as TXT",
        data=st.session_state.sequence_str,
        file_name="execution_sequence.txt",
        mime="text/plain"
    )




# Input for the container tool ID
st.sidebar.header("Helper 2 - Get Child Tool IDs of Container")

container_tool_id = st.sidebar.text_input("Enter Container Tool ID")
# Container instructions
st.sidebar.markdown("Fetch all child tool IDs of a container.")

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


# --------------------- Main Content ---------------------------
# --------------------- Main Content ---------------------------

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
            st.write(f"Loaded {len(df_nodes)} nodes and {len(df_connections)} connections.")
            progress_bar.progress(5)


            # Filter out unwanted tool types.
            df_nodes = df_nodes[~df_nodes["tool_type"].isin(["BrowseV2", "Toolcontainer"])]
            message_placeholder.write(f"After filtering, {len(df_nodes)} nodes remain.")
            st.write(f"After filtering browser and container, {len(df_nodes)} nodes remain.")

            # Generate Python code for the specified tool IDs.
            test_df = df_nodes.loc[df_nodes["tool_id"].isin(tool_ids)]
            message_placeholder.write(f"**Generating code for {len(test_df)} tool(s), it may take {len(test_df)*4} seconds...**")
            logging.debug(f"Generating code for {len(test_df)} tool(s) with tool IDs: {tool_ids}")

            # Generate execution sequence.
            execution_sequence = traverse_helper.get_execution_order(df_nodes, df_connections)
            logging.debug(f"Execution sequence generated with {len(execution_sequence)} steps.")
            message_placeholder.write(f"Execution sequence generated with {len(execution_sequence)} steps.")

            # Adjust the order of tool IDs based on the execution sequence.
            ordered_tool_ids = traverse_helper.adjust_order(tool_ids, execution_sequence)
            st.write(f"Tool IDs ordered has been adjusted based on execution sequence.")


            df_generated_code = prompt_helper.generate_python_code_from_alteryx_df(test_df, df_connections, progress_bar, message_placeholder)

            # If "tool_id" is missing in df_generated_code, insert it
            if "tool_id" not in df_generated_code.columns:
                logging.debug("Adding missing 'tool_id' column to generated code DataFrame.")
                df_generated_code.insert(0, "tool_id", test_df["tool_id"].values)

            message_placeholder.write("**Working on combining code snippets...**")

            # Combine code snippets for the specified tools.
            final_script, prompt = prompt_helper.combine_python_code_of_tools(tool_ids, df_generated_code, execution_sequence=ordered_tool_ids, extra_user_instructions=extra_user_instructions)
            message_placeholder.write("**Finished generating code!**")
            progress_bar.progress(100)
            st.success("Conversion succeeded! Scroll down to see your Python code.")
            st.code(final_script, language="python")
            st.header("Following a prompt was used to generate the code:")
            st.write("This app is using gpt-4o, if want better result. Please use following prompt in ChatGPT app with o1 or o3-mini-high model")
            st.code(prompt, language="python")

        except Exception as e:
            st.error("Conversion Error:")
            st.exception(e)
            logging.exception("Error during conversion process.")
