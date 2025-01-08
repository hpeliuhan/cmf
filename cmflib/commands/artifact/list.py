###
# Copyright (2024) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

import argparse
import os
import pandas as pd
import textwrap

from tabulate import tabulate
from typing import Union, List
from cmflib.cli.command import CmdBase
from cmflib import cmfquery
from cmflib.cmf_exception_handling import ( 
    PipelineNotFound,
    FileNotFound,
    ArtifactNotFound,
    DuplicateArgumentNotAllowed,
    MissingArgument,
    MsgSuccess
)

class CmdArtifactsList(CmdBase):
    def convert_to_datetime(self, df: pd.DataFrame, col_name: str) -> pd.DataFrame:
        """
        Function to convert a column to datetime format.
        Parameters:
        - df: The DataFrame containing the data.
        - col_name: The name of the column to convert to datetime.
        Returns:
        - The updated DataFrame with the specified column converted to datetime format.
        """  
        # Convert the col_name column to UTC datetime format.
        # The datetime is formatted as "Day DD Mon YYYY HH:MM:SS GMT"
        df=df.copy()
        df[col_name] = pd.to_datetime(df[col_name], unit='ms', utc=True).dt.strftime("%a %d %b %Y %H:%M:%S GMT")
        
        return df
    
    def display_table(self, df: pd.DataFrame) -> None:
        """
        Display the DataFrame in a paginated table format with text wrapping for better readability.
        Parameters:
        - df: The DataFrame to display.
        """
        # Rearranging columns
        updated_columns = ["id", "name", "type", "create_time_since_epoch", "url", "Commit", "uri"] 
        df = df[updated_columns]
        df = df.copy()
       
        # Wrap text in object-type columns to a width of 14 characters.
        # This ensures that long strings are displayed neatly within the table.
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].apply(lambda x: textwrap.fill(x, width=14) if isinstance(x, str) else x)

        total_records = len(df)
        start_index = 0  

        # Display up to 20 records per page for better readability. 
        # This avoids overwhelming the user with too much data at once, especially for larger mlmd files.
        while True:
            end_index = start_index + 20
            records_per_page = df.iloc[start_index:end_index]
            
            # Display the table.
            table = tabulate(
                records_per_page,
                headers=df.columns,
                tablefmt="grid",
                showindex=False,
            )
            print(table)

            # Check if we've reached the end of the records.
            if end_index >= total_records:
                print("\nEnd of records.")
                break

            # Ask the user for input to navigate pages.
            user_input = input("Press Enter to see more or 'q' to quit: ").strip().lower()
            if user_input == 'q':
                break
            
            # Update start index for the next page.
            start_index = end_index 

    def search_artifact(self, df: pd.DataFrame) -> Union[int, List[int]]:
        """
        Searches for the specified 'artifact_name' in the DataFrame and returns matching IDs.

        Parameters:
        - df: DataFrame to search within.

        Returns:
        - List of matching IDs or -1 if no matches are found.
        """
        # Example of a given sample 'artifact_name' --> artifacts/parsed/train.tsv:12345
        # These are the combinations we are implementing:
        # 1. artifacts/parsed/train.tsv
        # 2. train.tsv   
        # 3. artifacts/parsed/train.tsv:12345
        # 4. train.tsv:12345
        
        # In case of multiple occurrences of 'artifact_name', we need to store the IDs of all matching names.
        # For example, if "metrics" appears multiple times, we store all its IDs.
        matched_ids = []
        artifact_name = self.args.artifact_name[0].strip()
        for index, row in df.iterrows():
            # Extract the base name from the row.
            # eg. artifacts/parsed/train.tsv:12345 --> artifacts/parsed/train.tsv
            name =  row['name'].split(":")[0]      
            if artifact_name == name:             # Match the full path: artifacts/parsed/train.tsv
                matched_ids.append(row['id'])     
            elif artifact_name == name.split('/')[-1]:    # Match only the file name: train.tsv
                matched_ids.append(row['id'])
            elif artifact_name == row['name']:             # Match the full path with hash: artifacts/parsed/train.tsv:12345
                matched_ids.append(row['id'])
            elif artifact_name == row["name"].split('/')[-1]:   # Match only the file name with hash: train.tsv:12345
                matched_ids.append(row['id'])
        
        if len(matched_ids) != 0:
            return matched_ids
        return -1

    def run(self):
        
        # default path for mlmd file name
        mlmd_file_name = "./mlmd"
        current_directory = os.getcwd()
        if not self.args.file_name:         # If self.args.file_name is None or an empty list ([]). 
            mlmd_file_name = "./mlmd"       # Default path for mlmd file name.
        elif len(self.args.file_name) > 1:  # If the user provided more than one file name. 
                raise DuplicateArgumentNotAllowed("file_name", "-f")
        elif not self.args.file_name[0]:    # self.args.file_name[0] is an empty string ("").
                raise MissingArgument("file name")
        else:
            mlmd_file_name = self.args.file_name[0].strip()
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
        current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name):
            raise FileNotFound(mlmd_file_name, current_directory)
        # Creating cmfquery object.
        query = cmfquery.CmfQuery(mlmd_file_name)
        
        # Check if pipeline exists in mlmd.
        if self.args.pipeline_name is not None and len(self.args.pipeline_name) > 1:
                raise DuplicateArgumentNotAllowed("pipeline_name", "-p")
        elif not self.args.pipeline_name[0]:    # self.args.pipeline_name[0] is an empty string ("").
                raise MissingArgument("pipeline name")
        else:
            pipeline_name = self.args.pipeline_name[0]
        
        df = query.get_all_artifacts_by_context(pipeline_name)

        if df.empty:
            raise PipelineNotFound(pipeline_name)
        else:
            if not self.args.artifact_name:         # If self.args.artifact_name is None or an empty list ([]). 
                pass
            elif len(self.args.artifact_name) > 1:  # If the user provided more than one artifact_name. 
                raise DuplicateArgumentNotAllowed("artifact_name", "-a")
            elif not self.args.artifact_name[0]:    # self.args.artifact_name[0] is an empty string ("").
                raise MissingArgument("artifact name")
            else:
                artifact_ids = self.search_artifact(df)
                if(artifact_ids != -1):
                    # Multiple/Single artifact names exist with the same name.
                    for artifact_id in artifact_ids:
                        # Filter the DataFrame to retrieve rows corresponding to the current ID.
                        filtered_data = df.loc[df['id'] == artifact_id] 

                        # Converting "create_time_since_epoch" and "last_update_time_since_epoch" to datetime format.
                        filtered_data = self.convert_to_datetime(filtered_data, "create_time_since_epoch")
                        filtered_data = self.convert_to_datetime(filtered_data, "last_update_time_since_epoch")

                        # Rearranging columns: Start with fixed columns and appending the remaining columns.
                        updated_columns = ["id", "name", "type", "create_time_since_epoch", "url", "Commit", "uri", "last_update_time_since_epoch"] 
                        updated_columns += [ col for col in filtered_data.columns if col not in updated_columns]
                        
                        filtered_data = filtered_data[updated_columns]

                        # Drop columns that start with 'custom_properties_' and that contains NaN values
                        columns_to_drop = [col for col in filtered_data.columns if col.startswith('custom_properties_') and df[col].isna().any()]
                        filtered_data = filtered_data.drop(columns=columns_to_drop)

                        # Wrap text in object-type columns to a width of 30 characters for better readability.
                        for col in filtered_data.select_dtypes(include=['object']).columns:
                            filtered_data[col] = filtered_data[col].apply(lambda x: textwrap.fill(x, width=30) if isinstance(x, str) else x)
                        
                        # For a single artifact name, display the table in a horizontal format:
                        # Set 'id' as the index.
                        filtered_data.set_index("id", inplace=True)
                        # Transpose the DataFrame to make rows into columns.
                        filtered_data = filtered_data.T.reset_index()
                        # Rename the first column back to 'id' for consistency.
                        filtered_data.columns.values[0] = 'id'
                        
                        # Display the formatted and transposed table using the 'tabulate' library.
                        table = tabulate(
                            filtered_data,
                            headers=filtered_data.columns,  # Use column names as headers.
                            tablefmt="grid",                # Use grid format for table borders.
                            showindex=False,                # Do not display the default index.
                        )
                        print(table)
                        print()

                        user_input = input("Press Enter to see more records if exists or 'q' to quit: ").strip().lower()
                        if user_input == 'q':
                            break
                    return MsgSuccess(msg_str = "End of records..")
                else:
                    raise ArtifactNotFound(self.args.artifact_name)
        
        df = self.convert_to_datetime(df, "create_time_since_epoch")
        self.display_table(df)

        return MsgSuccess(msg_str = "Done.")


def add_parser(subparsers, parent_parser):
    ARTIFACT_LIST_HELP = "Displays artifacts from the MLMD file with a few properties in a 7-column table, limited to 20 records per page."

    parser = subparsers.add_parser(
        "list",
        parents=[parent_parser],
        description="Displays artifacts from the MLMD file with a few properties in a 7-column table, limited to 20 records per page.",
        help=ARTIFACT_LIST_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    required_argumets = parser.add_argument_group("required arguments")

    required_argumets.add_argument(
        "-p", 
        "--pipeline_name", 
        required=True,
        action="append",
        help="Specify pipeline name.", 
        metavar="<pipeline_name>", 
    )

    parser.add_argument(
        "-f", 
        "--file_name",
        action="append",
        help="Specify the absolute or relative path for the input MLMD file.",
        metavar="<file_name>",
    )

    parser.add_argument(
        "-a", 
        "--artifact_name", 
        action="append",
        help="Specify the artifact name to display detailed information about the given artifact name.",
        metavar="<artifact_name>",
    )

    parser.set_defaults(func=CmdArtifactsList)