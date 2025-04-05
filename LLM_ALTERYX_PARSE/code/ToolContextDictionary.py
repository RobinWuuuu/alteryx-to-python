comprehensive_guide = {
    "Dbfileinput": (
        r"""
            Input Data Tool: Task to detect the extension of the input file(s) used and generate script accordingly.
            The following two specifications are specific to CSV and Excel input files. AleXPy can use this knowledge to accurately interpret and translate such configurations into Python scripts.

            1. <Delimeter>,</Delimeter>: This tag specifies the delimiter used to separate values in input data of .csv format. In this case, a comma. This tag must always be available within the <FormatSpecificOptions></FormatSpecificOptions> tag.

            2. <ImportLine>1</ImportLine>: This tag determines the starting point for data import.
            When '1', it starts data from the first record, i.e. header=0 in Python.
            When '2', it starts from the second record, i.e. header=1 in Python, and similarly,
            For '5', it begins from the fifth record, i.e. header=4 in Python.
            Logic: <ImportLine> 'N' in ALteryx always sets header=(N-1) in Python, where header is a parameter of the Pandas file reading functionality.
            "header" here represents the Python pandas library's built in parameter, i.e. pd.read(file, header=0)

            3. Creation of 'FileName' column: 
            Check for 'OutputFileName=' attribute in the provided XML file format.
            
            3.1. If OutputFileName="", it means that the output file name is not specified, as denoted by the empty double-quotes ""; hence, there's no need to create such a column for the DataFrame within the Python script.
            3.2. If the string 'FileName' is found within this attribute, like OutputFileName="FileName", write the following Python code: df["FileName"] = os.path.splitext(os.path.basename(file))[0]
            3.3. If the string 'Path' is found within this attribute, like OutputFileName="Path", write the following Python code: df["FileName"] = os.path.abspath(file)

            DO NOT PROVIDE ANY OTHER COLUMN NAME OTHER THAN "FileName" FOR CREATING THIS ADDITIONAL COLUMN.

            4. Handling Missing Columns in Python:
            Case 1: For Excel Files
            - Missing columns in Excel files will be represented as F-series, for instance, F1, F2, F3, F4, etc.
            - If you encounter such F-series column names, include them in the Python code as Unnamed-series, i.e. "Unnamed: 0", "Unnamed: 1", "Unnamed: 2", "Unnamed: 3", etc..

            Case 2: For CSV Files
            - Missing columns in CSV files will be represented as Field-series, for instance, Field_1, Field_2, Field_3, Field_4, etc.
            - If you encounter such Field-series column names, include them in the Python code as Unnamed-series, i.e. "Unnamed: 0", "Unnamed: 1", "Unnamed: 2", "Unnamed: 3", etc..

            You job is to generate Python scripts always in the Unnamed-series format for all F1, F2, F3, F4, or Field_1, Field_2, Field_3, Field_4 encountered field names found in the provided file.

            Notes: 
            - When using an asterisk (*) as a wildcard while specifying a path for reading Excel files in Alteryx, it includes all files with the .xlsx extension in that directory. For instance, the path 'C:\Users\66023\OneDrive - Bain\Desktop\rishabhpanda\AleXPy\inputs\test\*.xlsx' will process all Excel files located in the specified folder, 'C:\Users\66023\OneDrive - Bain\Desktop\rishabhpanda\AleXPy\inputs\test\'
            - Always use base sheet names for writing Python scripts to access any input .csv or .xlsx file. The base sheet name is the name after excluding the '$' sign from the suffix of the Sheet name. For example, 'Sheet1$' must be used as 'Sheet1' in Python code. Similarly, 'Sheet2$$' must be used as 'Sheet2$' in Python code. We just aim to exclude the last occuring '$' sign before using the Sheet name.
            - DO NOT use parameters like 'error_bad_lines', 'warn_bad_lines' and 'quotechar' in the Python script. DO NOT INCLUDE THEM ELSE YOU WILL BE PENALIZED.
            - Strictly do not write print statements to preview the DataFrames. The generated Python script will only contain the necessary code to read the input file and store it in a DataFrame.
        """
        ),

    "Alteryxselect": (
        r"""
        Follow the provided instructions below:
        
        Step 1: Carefully Identify the deselected fields, fields which have `selected`= False are the deselected fields. Carefully Identify the selected fields, fields which have `selected`= True are the selected fields.
        Step 2: If the number of deselected fields is less than the number of selected fields, remove the deselected fields from the dataset. Else if the number of selected fields is less than the number of deselected fields, filter the dataset for the selected fields.
        Step 3: Align with the Python datatypes and column names for the selected field basis `type` and `rename` parameter respectively.
                Only align the python datatypes of those columns whose `type` parameter is present.
        Step 4: Use pd.to_datetime code snippet to convert columns in to date time format.
 
        Example -
            <SelectField field="BCN_Roll-up ID" selected="True" type="Int64" size="8"/>
            <SelectField field="ZI_IT_Flag" selected="True" rename="ZI_it_flag" type="V_String" size="8"/>
            <SelectField field="BCN_Cleaned Country_Rolled-up" selected="False"/>
            <SelectField field="BCN_Customer Flag" selected="False"/>
            <SelectField field="BCN_Sector_MM std_Rolled-up" selected="True"/>
 
        Python code -
        Step 1: If the number of deselected fields is less than the number of selected fields, remove the deselected fields from the dataset. Else if the number of selected fields is less than the number of deselected fields, filter the dataset for the selected fields.
                In this case, the deselected fields are less than the selected fields, hence we instantly drop them conveniently.
           deselected_columns = ["BCN_Customer Flag", "BCN_Cleaned Country_Rolled-up"]
        Step 2:
            df = df.drop(columns=deselected_columns)
        Step 3:
        # Align the data types and the column names
            df = df.rename(columns={"ZI_IT_Flag": "ZI_it_flag"})
            df["BCN_Roll-up ID"] = df["BCN_Roll-up ID"].astype('int64')
            df["ZI_it_flag"] = df["ZI_it_flag"].astype(str)
        
        ### Do not change the data type of column "BCN_Sector_MM std_Rolled-up" as `type` parameter is not present in this example.
 
        You have to STRICTLY follow the above example in order to generate python code.

        Note: Do not create dummy DataFrames to implement this tool. And ignore all fields with the name "*Unknown"
         """
    ),

    "Summarize": (
        r"""
         

            - Parse the XML configuration mentally to identify the fileds to be taken into consideration using "SummarizeField field=" attribute.
            - Identify the "action=" attribute to perform operations like  groupby, count, sum, mean, count distinct, min, max, median, mode, variance, etc. aggregation operations available in mathematics.
            - Identify the "rename=" attribute to rename the columns in the DataFrame after the grouping and aggregations are successfully carried out.

            Special Case:
            1. If there is no aggregation operation specified in the XML configuration and only groupby operations are happening, the default aggregation operation to be taken is 'count' on a given field. And later drop the column which contains the count values, since it is not required as it wasn't specified.
            For example, for a tag like <SummarizeField field="Column_1" action="GroupBy" rename="Column_1" />, the default aggregation operation is 'count' on 'Column_1'. The column 'Column_1' will be grouped by and the count of each unique value will be calculated. The column containing the count values will be dropped from the DataFrame.
            In this case the script will be: grouped_df = df.groupby(['Column_1']); grouped_df = grouped_df.size().reset_index().drop(0, axis=1)
            
            Another example, for a tag like:
                <SummarizeField field="Column_1" action="GroupBy" rename="Column_1" />
                <SummarizeField field="Column_2" action="GroupBy" rename="Column_2" />
            the default aggregation operation is 'count' on any of the given 'Column_1' or 'Column_2'. Then finally, column containing the count values will be dropped from the DataFrame so that we only have "Column_1" and "Column_2" left after a successful groupby operation.
            In this case the script will be: grouped_df = df.groupby(['Column_1', 'Column_2]); grouped_df = grouped_df.size().reset_index().drop(0, axis=1)

            Note: Do not create dummy DataFrames to implement this tool.
        """
    ),

    "Sort": (
        r"""
         

            Analyze the <SortInfo> tag to identify the fields used for sorting and their respective sorting order.
            
            For example:
            <SortInfo locale="0">
                <Field field="Column_1" order="Descending" />
                <Field field="Column_2" order="Ascending" />
                <Field field="Column_3" order="Ascending" />
            </SortInfo>

            In this case, the sorting is performed based on the following fields and order:
            Column_1 → Descending
            Column_2 → Ascending
            Column_3 → Ascending
            Extract and interpret similar sorting details from the XML structure to generate an equivalent Python code.

            Python implementation template:
            Example:
            # Define the sorting fields and their respective sorting order based on the Alteryx configuration and store them using lists
            sort_fields = ['Column_1', 'Column_2', 'Column_3']
            sort_order = [False, True, True]

            # Perform the sorting operation
            sorted_df = df.sort_values(by=sort_fields, ascending=sort_order)

            Note: Do not create dummy DataFrames to implement this tool.
        """
    ),

    "Unique": (
        r"""
         

            Analyze the <UniqueFields> tag within the XML file to identify the columns used for filtering unique values in a DataFrame.
            Utilize the 'subset' parameter where applicable to specify the columns on which uniqueness is enforced while generating the code.
        """
    ),

    "Runningtotal": (
        r"""
         

            Select the fields to Group By (Optional): Search for <GroupByFields> tag to identify the columns used for Grouping the data.
            Create Running Total: Search for <RunningTotalFields> tag to identify the columns used for computing the running total.
            Note: New columns are added with a "RunTot_" prefix to show running totals for each column selected within the <RunningTotalFields> tag.

            Refer the examples provided below for a better understanding.
            Example 1: If we aim to calculate the running total of a column named "Column_1", then the Python script will be: df['RunTot_Column_1'] = df['Column_1'].cumsum()
            Example 2: If we aim to calculate the running total of two columns named "Column_1" and "Column_2", then the Python script will be: df['RunTot_Column_1'] = df['Column_1'].cumsum(); df['RunTot_Column_2'] = df['Column_2'].cumsum()
            Example 3: If we aim to calculate the running total of a column named "Column_1" on top a groupby operation including columns "Column_ABC" and "Column_XYZ", then the Python script will be: df['RunTot_Column_1'] = df.groupby(['Column_ABC', 'Column_XYZ'])['Column_1'].cumsum()

            Note: Do not create dummy DataFrames to implement this tool.
        """
    ),

    "Crosstab": (
        r"""
         

            Crosstab Tool: AleXPy will use the pandas built-in pivot_table functionality to replicate the behavior of the Alteryx Crosstab Tool. It will:
            - Identify three type of fields; the 'Group By' fields, the 'Column Headers' field, and the 'Values' field.
            - Utilize pandas.pivot_table() with the identified parameters to cross tab the data.
            - Generate a Python script that exactly replicates the Crosstab operation, including aggregation functions wherever specified.

            Note: Do not create dummy DataFrames to implement this tool.
        """
    ),

    "Transpose": (
        r"""
         

            Transpose Tool: AleXPy will use the pandas built-in melt functionality to replicate the behavior of the Alteryx Transpose Tool. It will:
            - Identify the Key fields and Data fields.
            - Utilize pandas.melt() with the identified parameters to transpose the provided DataFrame.
            - Generate a Python script that exactly replicates the Transpose operation.
            - The parameters must be as defined below. The new columns must be assigned the string 'Name', and 'Value' as it is mentioned in the following template:
                id_vars=key_columns,  # The columns to keep fixed
                var_name='Name',      # Assigned string 'Name' for the transposed column labels
                value_name='Value'    # Assigned string 'Value' for the transposed data values

            Note 1: Ignore the "Unknown" columns.
            Note 2: Do not create dummy DataFrames to implement this tool.
        """
    ),

    "RecordID": (
        r"""
         

            Analyze the following tags to extract key details while attempting to create the record ID column for the DataFrame:
            <FieldName></FieldName>: Identifies the name of the record ID column.
            <StartValue></StartValue>: Specifies the initial value for the record ID.
            <FieldType></FieldType>: Determines the datatype of the record ID column.
            <Position></Position>: Defines the column's placement in the DataFrame:
                The value '0' inside the <Position> tag stands for zeroth column index of the DataFrame, which means we create the record ID column at extreme left of the DataFrame.
                The value '1' inside the <Position> tag stands for the last column index of the DataFrame, i.e. "len(df_false.columns)", which means we create the record ID column at extreme right of the DataFrame.

            Example 1: When column name is "RecordID", start value is 7 (say), and position is at extreme left, i.e. zero index:
                # Configuration details from Alteryx tool
                field_name = "RecordID"
                start_value = 7
                position = 0 # Position 0 means the new column should be at the extreme left

                # Generate the RecordID column starting from the specified start value
                df[field_name] = range(start_value, start_value + len(df))

                # Reorder columns to place the RecordID at the specified position
                columns = df.columns.tolist()
                columns.insert(position, columns.pop(columns.index(field_name)))
                df = df[columns] 

            Example 2: When column name is "RecordID", start value is 1 (say), and position is at extreme right, i.e. last column index:
                # Configuration details from Alteryx tool
                field_name = "RecordID"
                start_value = 1
                position = len(df.columns) # Position len(df.columns) means the new column should be at the extreme right

                # Generate the RecordID column starting from the specified start value
                df[field_name] = range(start_value, start_value + len(df))

                # Reorder columns to place the RecordID at the specified position
                columns = df.columns.tolist()
                columns.insert(position, columns.pop(columns.index(field_name)))
                df = df[columns]

            Summary:
            The <Position></Position> tag will determine the position:
            If the <Position></Position> tag is '0' within the XML then position = 0,
            and if the <Position></Position> tag is '1' within the XML then position = len(df.columns)

            Note:
            Do not create dummy DataFrames to implement this tool.
        """
    ),

    "Formula": (
        r"""
         

            Carefully refer the <FormulaFields></FormulaFields> tag to extract three key details: the formula being used, the datatype it is cast to, and the column(s) to which it is applied.
            Whenever formulae includes slicing or accessing the beggining or ending string parts, use Python's built-in .startswith() and .endswith() commands rather than slicing commands. For example, Right([Name],3) can be written as name.endswith(".3")

            Note: Do not create dummy DataFrames to implement this tool.
        """
    ),

    "Filter": (
        r"""
         

            Carefully refer the <Expression></Expression> tag to understand which field(s) are being used for filtration and what expression is being used to perform this filtration.
            Output format: As per Alteryx's definition, Rows of data that meet the condition are output to the True anchor. Rows of data that do not meet the condition are output to the False anchor.
            Therefore, return two DataFrames after a filter process has been carried out. One representing the true part and another representing the false part.

            Example Python template:
            mask = (expression)
            df_true = df[mask]
            df_false = df[~mask]

            Note: Do not create dummy DataFrames to implement this tool.
        """
    ),

    "Sample": (
    r"""
         

        Carefully refer the <Configuration> tag to understand three crucial tags: <Mode></Mode>, <N></N> and <GroupFields orderChanged= />.

        Generate Python code based on the specifications mentioned below:
        
        For cases where, <Mode>First</Mode>: Return every row in the data from the beginning of the data through row N.
        Example: If N=5, return the first 5 rows of the DataFrame.

        For cases where, <Mode>Last</Mode>: Return the last N rows in the data.
        Example: If N=3, return the last 3 rows of the DataFrame.

        For cases where, <Mode>Skip</Mode>: Return all the records from the data EXCEPT the first N rows.
        Example: If N=7, skip the first 7 rows of the DataFrame and return the remaining.

        For cases where, <Mode>Sample</Mode>: Return the first row of every group of N rows.
        Example: If N=2, It returns the first row among every group of two rows. Which, in this example are, row 1, row 3, row 5, etc...

        For cases where, <Mode>NPercent</Mode>: Return the FIRST N percent of rows.
        Example 1: If the number of records is 19, and N=55, calculate 55%*19 which is 10.45, then round it off to get 10 and hence return the FIRST 10 records.
        Example 2: If the number of records is 34, and N=19, calculate 19%*34 which is 6.46, then round it off to get 6 and hence return the FIRST 6 records.
        Example 3: If the number of records is 19, and N=8, calculate 8%*19 which is 1.52, then round it off to get 2 and hence return the FIRST 2 records.

        Note: Do not create dummy DataFrames to implement this tool.
    """
    ),

    "Union": (
        r"""
         

            Perform concatenation on the provided DataFrames using Pandas.
            Implementation Guide:
                1. Store the given DataFrames in a list.
                2. Use pd.concat() to merge them efficiently.
            
            Python Example:
            # List of DataFrames to concatenate
            dataframe_list = [df1, df2, df3, ...]  

            # Concatenating with index reset
            concatenated_df = pd.concat(dataframe_list, ignore_index=True)

            Note 1: Ensure all input DataFrames are compatible in structure (field names and their corresponding data types) before performing concatenation to avoid misalignment issues.
            Note 2: Do not create dummy DataFrames to implement this tool.
        """
    ),

    "Cleanse.yxmc": (
        r"""
         

            1. Check Box (135) -
                1.1. If set to True → Remove rows where all the values in the DataFrame are null.
                Example code:
                remove_null_rows = True/False
                if remove_null_rows:
                    df = df.dropna(how='all', axis=0)

                1.2. If set to False → No action is taken; the DataFrame remains unchanged.

            2. Check Box (136) -
                2.1. If set to True → Remove columns where all the values are null.
                Example code:
                remove_null_columns = True/False
                if remove_null_columns:
                    df = df.dropna(how='all', axis=1)
                
                2.2. If set to False → No action is taken; the DataFrame remains unchanged.

            3. List Box (11) - List of columns for which the following steps are followed - Check Box (84), Check Box (117), Check Box (15), Check Box (109), Check Box (122), Check Box (53), Check Box (58), Check Box (70), Check Box (77).
            
            4. Check Box (84) -
                4.1. If set to True → For columns specified in LIST BOX (11) that are recognized as string/character types, replace null (NaN) values with an empty string ("").
                Sample code template: 
                for col in columns_list:
                    if col in df.columns:  # Existence check
                        if pd.api.types.is_string_dtype(df[col]):
                            df[col].fillna("", inplace=True)

                4.2. If set to False → No action is taken; NaN values remain unchanged.

            5. Check Box (117) -
                5.1. If set to True → For columns specified in LIST BOX (11) that are recognized as numeric types, replace null (NaN) values with 0.
                Sample code template:
                for col in columns_list:
                    if col in df.columns:  # Existence check
                        if pd.api.types.is_numeric_dtype(df[col]):
                            df[col].fillna(0, inplace=True)

                5.2. If set to False → No action is taken; null (NaN) values remain unchanged.

            6. Check Box (15) -
                6.1. If set to True → For columns specified in LIST BOX (11), remove leading and trailing whitespaces from string fields.
                Example code: 
                for col in columns_list:
                    if col in df.columns:  # Existence check
                        if pd.api.types.is_string_dtype(df[col]):
                            df[col] = df[col].str.strip()

                6.2. If set to False → No action is taken; values remain unchanged.
            
            7. Check Box (109) -
                7.1. If set to True → For columns specified in LIST BOX (11), perform the following cleanup:
                    7.1.1. Replace tabs (\t) and line breaks (\n) with a single space
                    7.1.2. Replace multiple spaces with a single space

                7.2. If set to False → No action is taken; values remain unchanged.

            8. Check Box (122) -
                8.1. If set to True → For columns specified in LIST BOX (11), remove all whitespace
                Example code:
                for col in columns_list:
                    if col in df.columns:  # Existence check
                        if pd.api.types.is_string_dtype(df[col]):
                            df[col] = df[col].str.replace(r'\s+', '', regex=True)

                8.2. If set to False → No action is taken; values remain unchanged.

            9. Check Box (53) -
                9.1. If set to True → For columns specified in LIST BOX (11), remove all alphabetical characters (A-Z, a-z).
                Example code: for col in columns_list:
                                    df[col] = df[col].astype(str).str.replace(r'[A-Za-z]+', '', regex=True)
                
                9.2. If set to False → No action is taken; values remain unchanged.

            10. Check Box (58) -
                10.1. If set to True → For columns specified in LIST BOX (11), remove all numeric digits (0-9)
                Example code: for col in columns_list:
                                    df[col] = df[col].astype(str).str.replace(r'[0-9]+', '', regex=True)

                10.2. If set to False → No action is taken; values remain unchanged.

            11. Check Box (70) -
                11.1. If set to True → For columns specified in LIST BOX (11), remove all punctuation symbols (e.g., !@#$%^&*()_+-={}[]:;"'<>,.?/|).
                Example code:
                punct_regex = '[' + re.escape(string.punctuation) + ']'
                string_columns = [col for col in columns_list if df[col].dtype == 'object']
                df[string_columns] = df[string_columns].apply(lambda x: x.str.replace(punct_regex, '', regex=True) if x.dtype == 'object' else x)

                11.2. If set to False → No action is taken; punctuation remains unchanged.

            12. Check Box (77) -
                12.1. If Check Box (77) is False → Skip processing for both Check Box (77) and Drop Down (81).

                12.2. If Check Box (77) is True → For columns specified in LIST BOX (11), modify the text case based on the selection in Drop Down (81):
                    12.2.1. "upper" → Convert text to uppercase.
                    12.2.2. "lower" → Convert text to lowercase.
                    12.2.3. "title" → Convert text to title case (first letter capitalized).

            Note: Do not create dummy DataFrames to implement this tool.
        """
    ),

    "DateTime": (
        r"""
         

        Refer the <Configuration> block that defines how to convert date/time fields in a pandas DataFrame, mirroring the Alteryx DateTime tool functionality. Within this file:

        1. The input column name appears in <InputFieldName> (e.g., <InputFieldName>Column_1</InputFieldName>).
        2. The date/time format of the incoming string field is in <Format> (e.g., <Format>dd-MM-yyyy</Format>). Auto detect the datetime format for slashes ("/") or hyphens ("-") as separator and act accordingly. Example, "20/01/2040", "20-01-2040"
        3. The date/time format for the output field will be (yyyy-mm-dd) for standardization.
        4. The desired output column name is in <OutputFieldName> (e.g., <OutputFieldName>DateTime_Out</OutputFieldName>).

        Use this information to generate Python code that:

        1. Identify areas within this file to extract:
            1.1. The input column to be converted.
            1.2. The date/time format specified.
            1.3. The output column name for storing converted data.

        2. Input DateTime format is specified within <Format> tag. Reads the input column from the DataFrame and converts the values from the specified format (e.g., dd-MM-yyyy) to a standardized output format (yyyy-mm-dd).

        3. Output DateTime format will be (yyyy-mm-dd) for standardization.

        4. Creates a new column in the DataFrame with the name from <OutputFieldName>, storing the converted date/time values.

        5. Includes a try/except block so that any rows that fail conversion are assigned Null (or NaN/None), preserving the rest of the data.

        Make sure to handle common date/time patterns (e.g., MM/dd/yyyy, yyyy-MM-dd hh:mm:ss, etc.) appropriately.
        If any part of the file is missing or incorrect, your code should either handle that gracefully (e.g., by logging a warning) or default to assigning Null to the resulting column.
        Finally, produce a Python script replicating the functionality of the Alteryx DateTime tool.

        A random example script for your reference:
        Python script that correctly handles dates in the format "Day/Month/Year" (e.g., "20/01/2040") and converts them into "Year-Month-Day" ("2040-01-20").

        input_field = 'some_date_column'
        output_field = 'DateTime_Out'
        date_format = '%d/%m/%Y'  # Correct format for "20/01/2040"

        # Ensure DataFrame exists
        if input_field not in df.columns:
            raise KeyError(f"Column '{input_field}' not found in DataFrame")

        # Convert the date column
        df[output_field] = np.nan  # Initialize output column with NaN

        for index, date_str in df[input_field].iteritems():
            try:
                extracted_date = datetime.strptime(str(date_str), date_format)
                df.at[index, output_field] = parsed_date.strftime('%Y-%m-%d')  # Format as 'YYYY-MM-DD'
            except ValueError:
                df.at[index, output_field] = np.nan  # Assign NaN if conversion fails


        ADDITIONAL RESOURCES:
        # Mapping fo Alteryx date format to Python's strptime/strftime format
        format_mapping = {
            'MM-dd-yyyy': '%m-%d-%Y',
            'dd-MM-yyyy': '%d-%m-%Y',
            'yyyy-MM-dd': '%Y-%m-%d',
            'MM/dd/yyyy': '%m/%d/%Y',
            'yyyy-MM-dd hh:mm:ss': '%Y-%m-%d %H:%M:%S'
        }

        Note: Do not create dummy DataFrames to implement this tool.
        """
    ),

    "Weightedavg.yxmc": (
        r"""
         

            Identify the necessary fields:
                Step 1: Extract the field specified in the "Value" parameter (this is the numeric field for which the weighted average will be calculated).
                Step 2: Extract the field specified in the "Weight" parameter (this is the numeric field that provides the weight for averaging).
                Step 3: Identify all fields listed under the "GroupFields" parameter, which will be used to group the data before performing calculations.
            Perform the weighted average calculation:
                Step 4: Group the dataset based on the GroupFields (if provided).
                Step 5: Compute the weighted average using the formula:
                            Weighted Average= ∑(Value multiplied Weight)/∑ Weight
                Step 6: If no GroupFields are provided, compute a single weighted average across the entire dataset.
            Store the result:
                Step 7: Create a new column with the name provided in the "OutputFieldName" parameter and store the computed weighted average values in it.
            
            ###Example code for your reference###
                value_field = Column A  # Value Field (Numeric)
                weight_field = Column B  # Weight Field (Numeric)
                group_fields = [Column D, Column E, Column F]  # Grouping Fields
                output_field_name = Column C  # Output Field Name
            
                # Step 3: Compute the Weighted Average by Group
                if group_fields:
                    df1 = df.groupby(group_fields).apply(
                        lambda x: (x[value_field] * x[weight_field]).sum() / x[weight_field].sum()
                    ).reset_index().rename(columns={0: output_field_name})
                else:
                    # Step 4: Compute a single weighted average across the entire dataset if no grouping fields exist
                    weighted_average_value = (df[value_field] * df[weight_field]).sum() / df[weight_field].sum()
                    df1 = pd.DataFrame({output_field_name: [weighted_average_value]})


            Note: Do not create dummy DataFrames to implement this tool.
    """
    ),

    "Joinmultiple": (
        r"""
         

        Context and Requirements
        You aim to replicate Alteryx's “Join Multiple Tool” in Python for any number of input DataFrames. The tool has several key parameters:

        1. JoinByRecPos
        1.1. True: Join rows by record position (i.e., row index).
        1.2. False: Join rows by one or more specified field(s) (e.g., "Product ID").

        2. OutputJoinOnly
        2.1. True: Only include rows that match across all inputs (like an inner join across multiple tables).
        2.2. False: Perform a full outer join, including all rows (non-matching rows from some inputs appear with NaN/nulls in the other inputs' columns).

        3. CartesianMode
        3.1. Allow:
        - The script allows a cartesian (multidimensional) join to occur if the join fields do not match across inputs (i.e., it creates all possible combinations).
        - No warning or error is produced in this scenario.

        3.2. Warn:
        - If a cartesian (multidimensional) join occurs, the script should log or print a warning indicating that such a join took place.
        - The process continues and produces the cartesian-joined result.

        3.3. Error:
        - If a cartesian (multidimensional) join is detected, the script should raise an error and stop further processing.

        Core Functionality
        A Python script must:
        1. Accept multiple input datasets (e.g., a list of DataFrames or file paths).
        
        2. Determine the join type based on OutputJoinOnly:
        - Inner-like join (if True) or
        - Full outer join (if False).
        
        3. Determine how to handle cartesian joins based on CartesianMode:

        4. Perform the join:
        - If JoinByRecPos=True, join on row indices (record positions).
        - If JoinByRecPos=False, join on the specified join field(s).
        - If there is a risk of a cartesian product (e.g., mismatched or missing keys), handle according to CartesianMode.

        5. Validate join fields (if JoinByRecPos=False), ensuring each input contains the required fields. If any required field is missing, raise an exception.

        6. Column Renaming and Preservation:
        - Unique Prefixes: Assign each input field a unique prefix, such as ('', 'Input_#2_', 'Input_#3_', 'Input_#4_', etc...'), based on the order in which the inputs are provided. The columns from the first input DataFrame must retain their original names unless specified some other name in the "rename=" clause. Input #2’s columns are automatically prefixed with Input_#2_., Similarly, Input #3’s columns are automatically prefixed with Input_#3_, and so on...
          To achieve this, rename the columns from the second DataFrame onwards beforehand.
          # Rename columns in df1 to add a prefix
            df2_renamed = df1.rename(columns=lambda x: f"Input_#2_{x}" if x != "Example_Column" else x)
            df3_renamed = df2.rename(columns=lambda x: f"Input_#3_{x}" if x != "Example_Column" else x)
            df4_renamed = df2.rename(columns=lambda x: f"Input_#4_{x}" if x != "Example_Column" else x)
            .
            .
            .
            And so on...

        - Handling Shared Field Names: If multiple inputs share the same field name, the first input can retain its original field name, while each subsequent input's field is renamed with its respective prefix (e.g., Input_#2_FieldName, Input_#3_FieldName, etc.). This ensures that identical field names from different inputs do not collide in the final output.
        - Ignore columns shown as “*Unknown”.
        - Consistency Across Inputs: Apply the same renaming logic to all inputs (1 through N) so the final dataset clearly indicates which columns originated from which input.

        7. Store the result in a DataFrame directly without creating any additional list for specific selected columns.

        Instructions:
        Generate a Python script that:
        1. Accepts a list of input DataFrames and parameters:
        - join_by_rec_pos (bool)
        - output_join_only (bool)
        - cartesian_mode (str; one of "Allow", "Warn", or "Error")
        - join_fields (list of strings if join_by_rec_pos=False)

        2. Implements the multi-input join logic:
        - Row-index join if join_by_rec_pos=True; field-based join if join_by_rec_pos=False.
        - Inner-like or full outer join based on output_join_only.
        - Detect cartesian joins and handle them according to cartesian_mode.

        3. Renames columns from each input with an appropriate prefix or user-defined rename rules.

        4. Returns the final merged DataFrame.


        Important Notes:
        a) Do not create any form of sample data for incorporating this tool.
        For example, do not create anything like:
            # Sample input DataFrames
            df1 = pd.DataFrame({
                'Column_1': [1, 2, 3],
                'Column_2': ['A', 'B', 'C']
            })

            df2 = pd.DataFrame({
                'Column_1': [1, 2, 4],
                'Column_2': ['X', 'Y', 'Z'],
                'Column_3': ['Brand1', 'Brand2', 'Brand3']
            })

        b) Do not filter the final result of this tool for selected columns. Don't do it.
        For example, do not generate script for selected columns like:
            # Select and rename columns as specified
            selected_columns = [
                'Column_1', 'Column_2', 'Column_3',
                'Column_4', 'Column_5', 'Column_6'
            ]

            # Filter the result to include only selected columns
            result = result[selected_columns]
        """
    ),

    "Join":  (
        r"""
         
        
        Follow the INSTRUCTIONS below -
        1) For LEFT JOIN

        Step 1: Consider the DataFrames to be joined as df_left and df_right. Define primary keys separately for df_left and df_right
        Example:
        primary_keys_left = ["Column_1", "Column_2", etc...]
        primary_keys_right = ["Column_1", "Column_5", etc...]

        Step 2: Rename columns in df_right that are also present in df_left with "Right_" prefix
        Example:
        df_right = df_right.rename(columns=lambda x: f"Right_{x}" if x in df_left.columns else x)

        Step 3: Dynamically initialize the key
        # Determine if the primary key in df_right was renamed
        renamed_key = f"Right_{primary_keys_right[0]}" if primary_keys_right[0] in df_left.columns else primary_keys_right[0]

        Step 4: Perform a left_only join (entries that exist only in df_left). Then, filter for the "_merge" indicator and drop the unwanted "_merge" column. Finally, drop columns with all null values.
        Example:
        # Perform a left_only join (entries that exist only in df_left)
        left_only_join = df_left.merge(
            df_right, 
            left_on=primary_keys_left, 
            right_on=renamed_key
            how="left", 
            indicator=True
        )

        Step 5:
        # Filter for the "_merge" indicator and drop the unwanted "_merge" column
        left_only_join = left_only_join[left_only_join["_merge"] == "left_only"].drop(columns=["_merge"])

        Step 6:
        # Drop columns with all null values
        left_only_join = left_only_join.dropna(axis=1, how='all')

        Use a separator after left join as follows-
        # ===============================================================================

        2) For RIGHT JOIN

        Step 1: Consider the DataFrames to be joined as df_left and df_right. Define primary keys separately for df_left and df_right
        Example:
        primary_keys_left = ["Column_1", "Column_2", etc...]
        primary_keys_right = ["Column_1", "Column_5", etc...]

        Step 2: Rename columns in df_right that are also present in df_left with "Right_" prefix
        Example:
        df_right = df_right.rename(columns=lambda x: f"Right_{x}" if x in df_left.columns else x)

        Step 3: Dynamically initialize the key
        # Determine if the primary key in df_right was renamed
        renamed_key = f"Right_{primary_keys_right[0]}" if primary_keys_right[0] in df_left.columns else primary_keys_right[0]

        Step 4: Perform a right_only join (entries that exist only in df_right). Then, filter for the "_merge" indicator and drop the unwanted "_merge" column. Then, drop columns with all null values. Finally, normalize field names by removing the "Right_" prefix from every column.
        Example:
        # Perform a right_only join (entries that exist only in df_right)
        right_only_join = df_left.merge(
            df_right, 
            left_on=primary_keys_left, 
            right_on=f"Right_{primary_keys_right[0]}",  # Extracting the actual string
            how="right", 
            indicator=True
        )

        Step 5:
        # Filter for the "_merge" indicator and drop the unwanted "_merge" column
        right_only_join = right_only_join[right_only_join["_merge"] == "right_only"].drop(columns=["_merge"])

        Step 6:
        # Drop columns with all null values
        right_only_join = right_only_join.dropna(axis=1, how='all')

        Step 7:
        # Normalize field names by removing the "Right_" prefix from every column
        right_only_join.columns = right_only_join.columns.map(lambda col: col.replace("Right_", ""))

        Use a separator after right join as follows-
        # ===============================================================================

        2) For INNER JOIN

        Step 1: Consider the DataFrames to be joined as df_left and df_right. Define primary keys separately for df_left and df_right
        Example:
        primary_keys_left = ["Column_1", "Column_2", etc...]
        primary_keys_right = ["Column_1", "Column_5", etc...]

        Step 2: Perform an inner join.
        Example:
        # Perform an inner join
        inner_join = df_left.merge(
            df_right, 
            left_on=f"{primary_keys_left[0]}",
            right_on=f"{primary_keys_right[0]}",
            how="inner"
        )

        Step 3: Deselection, Typecasting and/or Renaming (IFF specified using selected="False", 'type=' and 'rename=' attributes respectively).
        
        3.1. Deselected fields mentioned in the field= attribute (marked by selected="False" attribute) must be dropped from the inner_join DataFrame. IGNORE columns marked as selected="True".
        If any field undergoes deselection, and any other operation like renaming or typecasting, simply perform the drop operation corresponding to deselection and no other operation is required as it does not make sense to treat already dropped columns. 
        
        3.2. Typecasted fields mentioned in the field= attribute (marked by type= attribute) must be typecasted in the inner_join DataFrame as per their data types provided.
        
        Special Cases: For cases where a field undergoes both renaming and typecasting, first do the typecasting, and then perform the renaming.
        
        For example, if you find a case as follows:
        <SelectField field="Right_Column_1" selected="True" rename="ABC_Name" input="Right_" type="Int64" size="8" />
        
        In such cases first typecast the column with the exact name specified in the (field=) attribute, in this case, "Right_Column_1":
        inner_join["Right_Column_1"] = inner_join["Right_Column_1"].astype('int64')

        Then rename that same field, in this case "Right_Column_1" as per the (rename=) attribute, in this case "ABC_Name".
        Here, "Right_Column_1" is the (field=) name and "ABC_Name" is the new name (rename=).
        inner_join = inner_join.rename(columns={
            "Right_Column_1": "ABC_Name"
        })

        3.3. Renamed fields mentioned in the field= attribute (marked by rename= attribute) must be renamed in the inner_join DataFrame as per their new names provided.
    
        Final Notes:
        Do not create dummy DataFrames to implement this tool.

        Step 8: Assign join outputs to specific tools.
            - Use **left_only_join** as input to the specified tool (if any).
            - Use **inner_join** as input to the specified tool (if any).
            - Use **right_only_join** as input to the specified tool (if any).

        """
        ),

    "Alteryxdbfileoutput": (
        r"""
        Headings: Add Heading corresponding to the tool ID. For example, if the tool ID is 16, and if it is a reading tool, then the heading before code generation must be as follows
        # ===============================================================================
        # [Tool 16] → Read the CSV file into a DataFrame
        # ===============================================================================
        
        Check for the proper extension of the file mentioned to get an understanding of which format the user desires to generate an output with.

        A) If it is a "CSV" type export, follow the below Python template:
        Step 1: Initialize the configuration parameters
        # Configuration parameters from the Alteryx tool
        file_path = r'' # Example: C:\\Users\\...\\file_name.csv
        delimiter = '' # Example: ','
        line_terminator = ''  # CRLF, example, '\r\n'
        quote_all = # Set as True or False
        header = # Set as True or False
        encoding = ''  # Example: for CodePage 28591, set as 'ISO-8859-1'
        write_bom = True

        Step 2: Write the DataFrame to a CSV file with the specified configurations
        # Write the DataFrame to a CSV file with the specified configurations
        data.to_csv(
            file_path,
            sep=delimiter,
            index=False,
            line_terminator=line_terminator,
            quoting=(1 if quote_all else 0),  # 1 for all, 0 for minimal quoting
            header=header,
            encoding=encoding
        )

        Step 3: Add BOM whenever required
        # Add BOM whenever required
        if write_bom:
            with open(file_path, 'r+b') as f:
                content = f.read()
                f.seek(0, 0)
                f.write(b'\xEF\xBB\xBF' + content)

        
        B) If it is an "XLSX" type export, follow the below Python template:
        Step 1: Initialize the configuration parameters
        # Configuration parameters from the Alteryx tool
        file_path = r'' # Example: 'C:\\Users\\file_name.xlsx'
        sheet_name = '' # Example: 'Sheet1' or any other given sheet name
        preserve_format = # Set as True or False
        skip_field_names = # Set as True or False
        output_option = ''  # Example Options: 'Create', 'Overwrite', 'Append'

        Step 2: Determine the mode for writing to the Excel file
        # Determine the mode for writing to the Excel file
        if output_option == 'Create':
            mode = 'w'
        elif output_option == 'Overwrite':
            mode = 'w'
        elif output_option == 'Append':
            mode = 'a'
        else:
            raise ValueError("Invalid output option specified.")

        Step 3: Write DataFrame to Excel file
        # Write DataFrame to Excel file
        with pd.ExcelWriter(file_path, engine='openpyxl', mode=mode) as writer:
            df_tool_26.to_excel(writer, sheet_name=sheet_name, index=False, header=not skip_field_names)
        """
    ),
    "BrowseV2": (
        r"""
        Browsev2 Tool:
        - Purpose: This tool is used to preview or inspect data within the workflow.
        - Instructions: Generate Python code that displays a summary or preview of a DataFrame.
          For example, use df.head() to display the first few rows.
        - Requirements: Do not include additional debugging output; simply return or display the preview data.
        """
    ),
    "Dbfileoutput": (
        r"""
        Dbfileoutput Tool:
        - Purpose: This tool writes output data to a file.
        - Instructions:
            1. Detect the file extension (e.g., .csv or .xlsx) from the configuration.
            2. For CSV files, generate code using DataFrame.to_csv() with proper parameters such as delimiter, header, index, encoding, etc.
            3. For Excel files, generate code using pd.ExcelWriter() and DataFrame.to_excel() with the appropriate mode (Create/Overwrite/Append).
        - Requirements: Ensure that the generated code reproduces the export configuration exactly as specified.
        """
    ),
    "Textbox": (
        r"""
        Textbox Tool:
        - Purpose: This tool is used to display static text or messages within the workflow.
        - Instructions: Generate Python code that assigns the provided text to a variable or prints it.
          For example: message = "Your message here" or simply print("Your message here").
        - Requirements: Do not include additional formatting or debugging information.
        """
    ),
    "Multifieldformula": (
        r"""
        Multifieldformula Tool:
        - Purpose: This tool applies the same formula to multiple fields within the dataset.
        - Instructions:
            1. Identify the list of target fields on which the formula should be applied.
            2. Generate Python code that iterates over these fields and applies the specified formula.
               Use vectorized operations or the df.apply() method as appropriate.
        - Requirements: The code should update the DataFrame for all specified fields without creating dummy data.
        """
    ),
    "Appendfields": (
        r"""
        Appendfields Tool:
        - Purpose: This tool appends additional columns from a secondary dataset to the primary dataset.
        - Instructions:
            1. Generate Python code that uses pd.concat() along axis=1 to merge two DataFrames.
            2. Ensure that the DataFrame indexes are aligned so that the rows match correctly.
        - Requirements: The final script should simply append columns without additional filtering or reordering.
        """
    ),
    "Textinput": (
        r"""
        Textinput Tool:
        - Purpose: This tool captures user-provided text input within the workflow.
        - Instructions: Generate Python code that assigns the text input to a variable (e.g., input_text = "user provided text").
        - Requirements: Keep the code simple without extra validation or formatting.
        """
    ),
    "Texttocolumns": (
        r"""
        Texttocolumns Tool:
        - Purpose: This tool splits a single text field into multiple columns based on a delimiter.
        - Instructions:
            1. Identify the target text field and the delimiter from the configuration.
            2. Generate Python code using the pandas Series.str.split() method with expand=True to split the field.
            3. Assign appropriate column names to the new columns.
        - Requirements: The resulting DataFrame must include the new columns without modifying the original data beyond the split.
        """
    )
}