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

from cmflib.cli.command import CmdBase
from cmflib import cmfquery

class CmdArtifactsList(CmdBase):
    def update_dataframe(self, df):
        for c in df.columns:
            if c.startswith('custom_properties_'):
                df.rename(columns = {c:c.replace('custom_properties_','')}, inplace = True)
            else:
                df = df.drop(c, axis = 1)
        return df

    def search_artifact(self, df):
        for index, row in df.iterrows():
            name = row['name'].split(":")[0]
            file_name = name.split('/')[-1]
            if file_name == self.args.artifact_name:
                return row['id']
        return -1

    def run(self):
        current_directory = os.getcwd()
        # default path for mlmd file name
        mlmd_file_name = "./mlmd"
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
            current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name):
            return f"ERROR: {mlmd_file_name} doesn't exists in {current_directory} directory."

        # Creating cmfquery object
        query = cmfquery.CmfQuery(mlmd_file_name)

        df = query.get_all_artifacts_by_context(self.args.pipeline_name)

        if not df.empty:
            if self.args.artifact_name:
                artifact_id = self.search_artifact(df)
                if(artifact_id != -1):
                    df = df.query(f'id == {int(artifact_id)}')
                else:
                    df = "Artifact name does not exist.."
        else:
            df = "Pipeline does not exist..."

        if not isinstance(df, str):
            if self.args.long:
                pd.set_option('display.max_rows', None)  # Set to None to display all rows
                pd.set_option('display.max_columns', None)  # Set to None to display all columns
            else:
                df = self.update_dataframe(df)
        return df

def add_parser(subparsers, parent_parser):
    ARTIFACT_LIST_HELP = "Display list of artifact as present in current mlmd"

    parser = subparsers.add_parser(
        "list",
        parents=[parent_parser],
        description="Display artifact list",
        help=ARTIFACT_LIST_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    required_argumets = parser.add_argument_group("required arguments")

    required_argumets.add_argument(
        "-p", 
        "--pipeline_name", 
        required=True,
        help="Specify pipeline name.", 
        metavar="<pipeline_name>", 
    )

    parser.add_argument(
        "-f", "--file_name", help="Specify mlmd file name.", metavar="<file_name>",
    )

    parser.add_argument(
        "-a", 
        "--artifact_name", 
        help="Specify artifact name.", 
        metavar="<artifact_name>",
    )

    parser.add_argument(
        "-l", 
        "--long", 
        action='store_true',
        help="Display detailed summary of artifact",
    )

    parser.set_defaults(func=CmdArtifactsList)