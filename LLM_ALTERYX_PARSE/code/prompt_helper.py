# Print working directory
import os
import sys
print(os.getcwd())

from code.traverse_helper import get_input_name, get_output_name
import pandas as pd
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from code.ToolContextDictionary import comprehensive_guide
import streamlit as st


def create_tool_io_template(df_connections, tool_id):
    """
    For a given tool_id, create a template string describing its inputs and outputs.
    The template will use get_input_name and get_output_name to obtain the names.

    Example output:
    "This tool (tool id 583) has 2 input(s): df_580_Output connects to the 'Left', df_582_Output connects to the 'Right'.
     And the 1st output is df_583_Join."
    """
    # Use the helper functions to get input and output names
    input_details = get_input_name(df_connections, tool_id)
    output_details = get_output_name(df_connections, tool_id)

    num_inputs = len(input_details)
    # Build input details string
    if num_inputs == 0:
        input_str = "No inputs"
    else:
        input_str_list = [f"{inp} connects to the '{typ}'" for inp, typ in input_details]
        input_str = ", ".join(input_str_list)

    # Build output details string with ordinal numbers
    num_outputs = len(output_details)
    if num_outputs == 0:
        output_str = "No outputs"
    else:
        output_str_list = []
        for i, out in enumerate(output_details):
            # Determine ordinal representation
            if i == 0:
                ordinal = "1st"
            elif i == 1:
                ordinal = "2nd"
            elif i == 2:
                ordinal = "3rd"
            else:
                ordinal = f"{ i +1}th"
            output_str_list.append(f"name the {ordinal} output as {out}")
        output_str = ", ".join(output_str_list)

    template_text = (f"This tool with id {tool_id} has {num_inputs} input(s), their variable name is {input_str}. Use {input_str} as the input for this tool "
                     f"And {output_str}.")
    return template_text


def generate_python_code_from_alteryx_df(df_nodes, df_connections, progress_bar=None):
    """
    Convert Alteryx tool configurations in a DataFrame to equivalent Python code,
    incorporating I/O details so the LLM knows which dataframes are expected.

    Parameters:
        df_nodes (pd.DataFrame): DataFrame containing columns 'tool_id', 'tool_type', and 'text'.
        progress_bar (st.progress): Optional Streamlit progress bar to update during processing.

    Returns:
        pd.DataFrame: A DataFrame with columns 'tool_id', 'tool_type', and 'python_code'.
    """
    # Define a prompt template with an additional_instructions placeholder.
    template = """
    You are an expert data engineer. Convert the following Alteryx tool configuration into equivalent Python code using open-source libraries.
    Tool type: {tool_type}
    Configuration details: {config_text}
    I/O details: {io_info}
    Additional instructions: {additional_instructions} In the <DefaultAnnotationText> element, there is a text field that contains the high level description of the tool but it could be empty. You can keep it as comment in the code.
    
    Rules:
    1. Please return only the Python code that reproduces the functionality of this tool.
    2. Don't include any explanations or comments.
    3. Don't include any import statements.
    4. Don't include any function definitions or docstrings.
    5. Don't include sample data, just the code.
    """

    prompt_template = PromptTemplate(
        input_variables=["tool_type", "config_text", "io_info", "additional_instructions"],
        template=template
    )

    # Initialize the ChatOpenAI LLM using your chosen model.
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")

    # Create the LangChain LLMChain.
    chain = LLMChain(llm=llm, prompt=prompt_template)

    results = []
    total_tools = len(df_nodes)  # Total number of tools to process
    progress_value = 0.05  # Initial progress value
    # Process each node in the DataFrame.
    for index, row in df_nodes.iterrows():
        tool_name = row["tool_type"]
        # Inject additional instructions if available in the dictionary.
        additional_instructions = (
            f'Refer to this additional information for "{tool_name}" tool - {comprehensive_guide[tool_name]}'
            if tool_name in comprehensive_guide else ""
        )
        # Create the I/O description using the helper function.
        io_info = create_tool_io_template(df_connections, row["tool_id"])

        generated_code = chain.run(
            tool_type=row["tool_type"],
            config_text=row["text"],
            io_info=io_info,
            additional_instructions=additional_instructions
        ).strip()

        results.append({
            "tool_id": row["tool_id"],
            "tool_type": row["tool_type"],
            "python_code": generated_code
        })

        
        # Update progress bar
        if progress_bar is not None:
            progress_value += (1 / total_tools)*0.8
            progress_bar.progress(min(max(progress_value, 0.0), 1.0))  # Clamp the value between 0.0 and 1.0

    return pd.DataFrame(results)


def combine_python_code_of_tools(tool_ids, df_generated_code, extra_user_instructions="", model="gpt-4o"):
    """
    Combine the Python code for multiple tool IDs into a single script using an LLM.

    Parameters:
        tool_ids (list): A list of tool IDs (str or int) you want to combine.
        df_generated_code (pd.DataFrame): DataFrame containing columns:
                                          'tool_id' and 'python_code'.
                                          Each row holds Python code for a particular tool.
        extra_user_instructions (str): Additional instructions for the code generation.
    Returns:
        str: A single string with the merged Python code.
    """

    # 1) Gather the code snippets for each tool in the specified order.
    #    We'll just concatenate them in the prompt for the LLM.
    code_snippets = []
    for tool_id in tool_ids:
        # Filter for the row matching this tool_id
        subset = df_generated_code.loc[df_generated_code["tool_id"] == tool_id, "python_code"]
        if not subset.empty:
            code_snippets.append(subset.iloc[0])
        else:
            code_snippets.append(f"# No code found for tool {tool_id}")

    # Create a single string with all code snippets.
    all_tool_code = "\n\n".join(
        f"Tool {tool_id} code:\n{snippet}" for tool_id, snippet in zip(tool_ids, code_snippets)
    )
    if not extra_user_instructions:
        extra_user_instructions = ''
    # 2) Create a prompt template that instructs the LLM to merge the code snippets.
    template = """
    You are an expert data engineer. We have multiple python code snippets translated from different Alteryx tools, and we want to combine them into a single coherent Python script.
    
    Code snippets:
    {all_tool_code}
    
    Extra user instructions: {extra_user_instructions} 

    Requirements:
    1. Please return only the combined Python script, don't use ```python ``` to make it a code block. Just return the code.
    2. Do not add any import statements (assume they exist).
    3. Do not write function definitions or docstrings unless needed to chain code together.
    4. Merge them in a logical order that respects typical data processing flow (if possible).
    5. Eliminate redundant or conflicting statements.
    6. For each tool, add very concise comment to describe the tool's purpose if not obvious.

    Provide only the merged code below:
    """

    prompt = PromptTemplate(
        input_variables=["all_tool_code", "extra_user_instructions"],
        template=template
    )

    # 3) Initialize the LLM and chain. Adjust your model or temperature as needed.
    #    For example, using a hypothetical "gpt-4o-mini" model from your environment:
    llm = ChatOpenAI(temperature=0, model_name=model)
    chain = LLMChain(llm=llm, prompt=prompt)

    # 4) Run the chain to combine the code.
    merged_code = chain.run(all_tool_code=all_tool_code, extra_user_instructions=extra_user_instructions).strip()
    return merged_code
