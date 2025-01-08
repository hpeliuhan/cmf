###
# Copyright (2022) Hewlett Packard Enterprise Development LP
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

#!/usr/bin/env python3
import argparse
import json
import os

from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.cmf_exception_handling import (
    PipelineNotFound,
    FileNotFound,
    DuplicateArgumentNotAllowed,
    MissingArgument,
    NoChangesMadeInfo,
    MetadataExportToJson
)

# This class export local mlmd data to a json file
class CmdMetadataExport(CmdBase):
    def create_full_path(self, current_directory: str, json_file_name: str) -> str:
        if not os.path.isdir(json_file_name):
            temp = os.path.dirname(json_file_name)
            current_directory = './'
            if temp != "":
                current_directory = temp
            if os.path.exists(current_directory):
                full_path_to_dump  = json_file_name
                return full_path_to_dump
            else:
                return f"{current_directory} doesn't exists."
        else:
            return "Provide path with file name."
        
    def run(self):
        current_directory = os.getcwd()
        full_path_to_dump = ""

        if not self.args.file_name:         # If self.args.file_name is None or an empty list ([]). 
            mlmd_file_name = "./mlmd"       # Default path for mlmd file name.
        elif len(self.args.file_name) > 1:  # If the user provided more than one file name.   
            raise DuplicateArgumentNotAllowed("file_name", "-f")
        elif not self.args.file_name[0]:    # self.args.file_name[0] is an empty string ("").
            raise MissingArgument("file name")
        else:
            mlmd_file_name = self.args.file_name[0].strip() # Removing starting and ending whitespaces.
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
        
        current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name): 
            raise FileNotFound(mlmd_file_name, current_directory)

        # Initialising cmfquery class.
        query = cmfquery.CmfQuery(mlmd_file_name)

        # Check if pipeline exists in mlmd .
        if self.args.pipeline_name is not None and len(self.args.pipeline_name) > 1:   
            raise DuplicateArgumentNotAllowed("pipeline_name", "-p")
        elif not self.args.pipeline_name[0]:    # self.args.pipeline_name[0] is an empty string (""). 
            raise MissingArgument("pipeline name")
        else:
            pipeline_name = self.args.pipeline_name[0]
        
        pipeline = query.get_pipeline_id(pipeline_name)

        if pipeline > 0:
            if not self.args.json_file_name:         # If self.args.json_file_name is None or an empty list ([]). 
                json_file_name = self.args.json_file_name
            elif len(self.args.json_file_name) > 1:  # If the user provided more than one json file name. 
                raise DuplicateArgumentNotAllowed("json file", "-j")
            elif not self.args.json_file_name[0]:    # self.args.json_file_name[0] is an empty string ("").  
                raise MissingArgument("json file")
            else:
                json_file_name = self.args.json_file_name[0].strip()

            # Setting directory where mlmd file will be dumped.
            if json_file_name:
                if not json_file_name.endswith(".json"):
                    json_file_name = json_file_name+".json" # Added .json extention to json file name.
                if os.path.exists(json_file_name): 
                    userRespone = input("File name already exists do you want to continue press yes/no: ")
                    if userRespone.lower() == "yes":    # Overwrite file.
                        full_path_to_dump = self.create_full_path(current_directory, json_file_name)
                    else: 
                        raise NoChangesMadeInfo()
                else:  
                    full_path_to_dump = self.create_full_path(current_directory, json_file_name)
            else: 
                # Checking whether a json file exists in the directory based on pipeline name.
                if os.path.exists(f"{pipeline_name}.json"): 
                    userRespone = input("File name already exists do you want to continue press yes/no: ")
                    if userRespone.lower() == "yes":
                        full_path_to_dump = os.getcwd() + f"/{pipeline_name}.json"
                    else:
                        raise NoChangesMadeInfo()
                else:  
                    full_path_to_dump = os.getcwd() + f"/{pipeline_name}.json"

            # Pulling data from local mlmd file.
            json_payload = query.dumptojson(pipeline_name,None)

            # Write metadata into json file.
            with open(full_path_to_dump, 'w') as f:
                f.write(json.dumps(json.loads(json_payload),indent=2))
                return MetadataExportToJson(full_path_to_dump)
        else:
            raise PipelineNotFound(pipeline_name)
            


def add_parser(subparsers, parent_parser):
    PULL_HELP = "Exports local mlmd's metadata to a json file."

    parser = subparsers.add_parser(
        "export",
        parents=[parent_parser],
        description="Export local mlmd's metadata in json format to a json file.",
        help=PULL_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "-p",
        "--pipeline_name",
        action="append",
        required=True,
        help="Specify Pipeline name.",
        metavar="<pipeline_name>",
    )

    parser.add_argument(
        "-j",
        "--json_file_name",
        action="append",
        help="Specify output json file name with full path.",
        metavar="<json_file_name>",
    )

    parser.add_argument(
        "-f", 
        "--file_name", 
        action="append",
        help="Specify the absolute or relative path for the input MLMD file.", 
        metavar="<file_name>",
    )

    parser.set_defaults(func=CmdMetadataExport)
