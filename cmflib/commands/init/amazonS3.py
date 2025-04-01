###
# Copyright (2023) Hewlett Packard Enterprise Development LP
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
import os

from cmflib.cli.command import CmdBase
from cmflib.dvc_wrapper import (
    git_quiet_init,
    git_checkout_new_branch,
    git_initial_commit,
    git_add_remote,
    dvc_quiet_init,
    dvc_add_remote_repo,
    dvc_add_attribute,
    git_modify_remote_url,
)
from cmflib.utils.cmf_config import CmfConfig
from cmflib.utils.helper_functions import is_git_repo
from cmflib.cmf_exception_handling import Neo4jArgumentNotProvided, CmfInitComplete, CmfInitFailed, DuplicateArgumentNotAllowed, MissingArgument
import sys

class CmdInitAmazonS3(CmdBase):
    def run(self):
        # Reading CONFIG_FILE variable
        cmf_config = os.environ.get("CONFIG_FILE", ".cmfconfig")

        cmd_args = {
            "url": self.args.url,
            "access-key-id": self.args.access_key_id,
            "secret-key": self.args.secret_key,
            "git-remote-url": self.args.git_remote_url,
            "session-token" : self.args.session_token,
            "neo4j-user" : self.args.neo4j_user,
            "neo4j-password" :  self.args.neo4j_password,
            "neo4j_uri" : self.args.neo4j_uri
        }
        for arg_name, arg_value in cmd_args.items():
            if arg_value:
                if arg_value[0] == "":
                    raise MissingArgument(arg_name)
                elif len(arg_value) > 1:
                    raise DuplicateArgumentNotAllowed(arg_name,("--"+arg_name))

        # checking if config file exists
        if not os.path.exists(cmf_config):
            # writing default value to config file
            attr_dict = {}
            attr_dict["server-ip"] = "http://127.0.0.1:80"
            CmfConfig.write_config(cmf_config, "cmf", attr_dict)
        # if user gave --cmf-server-ip, override the config file
        if self.args.cmf_server_url:  
            attr_dict = {}
            attr_dict["server-ip"] = self.args.cmf_server_url
            CmfConfig.write_config(cmf_config, "cmf", attr_dict, True)
        # read --neo4j details and add to the exsting file
        if self.args.neo4j_user and self.args.neo4j_password and self.args.neo4j_uri:
            attr_dict = {}
            attr_dict["user"] = self.args.neo4j_user[0]
            attr_dict["password"] = self.args.neo4j_password[0]
            attr_dict["uri"] = self.args.neo4j_uri[0]
            CmfConfig.write_config(cmf_config, "neo4j", attr_dict, True)
        elif(
            not self.args.neo4j_user
            and not self.args.neo4j_password
            and not self.args.neo4j_uri
        ):
            pass
        else:
            raise Neo4jArgumentNotProvided
        output = is_git_repo()
        if not output:
            branch_name = "master"
            print("Starting git init.")
            git_quiet_init()
            git_checkout_new_branch(branch_name)
            git_initial_commit()
            git_add_remote(self.args.git_remote_url[0])
            print("git init complete.")
        else:
            git_modify_remote_url(self.args.git_remote_url[0])
            print("git init complete.")


        print("Starting cmf init.")
        dvc_quiet_init()
        repo_type = "amazons3"
        output = dvc_add_remote_repo(repo_type, self.args.url[0])
        if not output:
            raise CmfInitFailed
        print(output)
        dvc_add_attribute(repo_type, "access_key_id", self.args.access_key_id[0])
        dvc_add_attribute(repo_type, "secret_access_key", self.args.secret_key[0])
        dvc_add_attribute(repo_type, "session_token", self.args.session_token[0])
        status = CmfInitComplete()
        return status


def add_parser(subparsers, parent_parser):
    HELP = "Initialises Amazon S3 as artifact repository."

    parser = subparsers.add_parser(
        "amazonS3",
        parents=[parent_parser],
        description="This command initialises Amazon S3 bucket as artifact repository for CMF.",
        help=HELP,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "--url",
        required=True,
        action="append",
        help="Specify Amazon S3 bucket url.",
        metavar="<url>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--access-key-id",
        required=True,
        action="append",
        help="Specify Access Key Id.",
        metavar="<access_key_id>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--secret-key",
        required=True,
        help="Specify Secret Key.",
        action="append",
        metavar="<secret_key>",
        default=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--session-token",
        required=True,
        help="Specify Session Token.",
        metavar="<session_token>",
        action="append",
    )

    required_arguments.add_argument(
        "--git-remote-url",
        required=True,
        help="Specify git repo url. eg: https://github.com/XXX/example.git",
        action="append",
        metavar="<git_remote_url>",
        default=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--cmf-server-url",
        help="Specify cmf-server URL.",
        metavar="<cmf_server_url>",
        action="append",
        default=["http://127.0.0.1:80"],
    )
    parser.add_argument(
        "--neo4j-user",
        help="Specify neo4j user.",
        metavar="<neo4j_user>",
        action="append",
        # default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--neo4j-password",
        help="Specify neo4j password.",
        metavar="<neo4j_password>",
        action="append",
        # default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--neo4j-uri",
        help="Specify neo4j uri.eg bolt://localhost:7687",
        metavar="<neo4j_uri>",
        action="append",
        # default=argparse.SUPPRESS,
    )

    parser.set_defaults(func=CmdInitAmazonS3)
