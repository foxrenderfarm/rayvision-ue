# -*- coding: utf-8 -*-
"""A interface for ue."""

# Import built-in models
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import logging
import os
import sys
import time
from builtins import str
import threading
import shutil

from rayvision_log import init_logger
from rayvision_utils import constants
from rayvision_utils import utils
from rayvision_utils.cmd import Cmd
from rayvision_utils.exception import tips_code
from rayvision_utils.exception.error_msg import ERROR9899_CGEXE_NOTEXIST
from rayvision_utils.exception.exception import AnalyseFailError
from rayvision_utils.exception.exception import CGExeNotExistError
from rayvision_utils.exception.exception import CGFileNotExistsError
from rayvision_ue.constants import PACKAGE_NAME

VERSION = sys.version_info[0]


class AnalyzeUe(object):
    def __init__(self, cg_file, software_version, software_install_dir,
                 project_name, plugin_config, render_software="Unreal Engine",
                 local_os=None, workspace=None,
                 custom_exe_path=None,
                 platform="2",
                 logger=None,
                 log_folder=None,
                 log_name=None,
                 log_level="DEBUG"
                 ):
        """Initialize and examine the analysis information.

        Args:
            cg_file (str): Scene file path.
            software_version (str): Software version.
            software_install_dir (str): Software install dir.
            project_name (str): The project name.
            plugin_config (dict): Plugin information.
            render_software (str): Software name, 'Unreal Engine' by default.
            local_os (str): System name, linux or windows.
            workspace (str): Analysis out of the result file storage path.
            custom_exe_path (str): Customize the exe path for the analysis.
            platform (str): Platform num.
            logger (object, optional): Custom log object.
            log_folder (str, optional): Custom log save location.
            log_name (str, optional): Custom log file name.
            log_level (string):  Set log level, example: "DEBUG","INFO","WARNING","ERROR".
        """
        self.logger = logger
        if not self.logger:
            init_logger(PACKAGE_NAME, log_folder, log_name)
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(level=log_level.upper())

        self.check_path(cg_file)
        self.cg_file = cg_file

        self.render_software = render_software
        self.software_version = software_version
        self.software_install_dir = software_install_dir
        self.project_name = project_name
        self.plugin_config = plugin_config if plugin_config else {}

        local_os = self.check_local_os(local_os)
        self.local_os = local_os
        self.tmp_mark = str(int(time.time())) + str(self.get_current_id())
        workspace = os.path.join(self.check_workspace(workspace), self.tmp_mark)
        if not os.path.exists(workspace):
            os.makedirs(workspace)
        self.workspace = workspace

        if custom_exe_path:
            self.check_path(custom_exe_path)
        self.custom_exe_path = custom_exe_path

        self.platform = platform

        self.task_json = os.path.join(workspace, "task.json")
        self.tips_json = os.path.join(workspace, "tips.json")
        self.asset_json = os.path.join(workspace, "asset.json")
        self.upload_json = os.path.join(workspace, "upload.json")
        self.analyse_success_file = os.path.join(workspace, "analyze_sucess")
        if os.path.exists(self.analyse_success_file):
            shutil.rmtree(self.analyse_success_file)
        self.tips_info = {}
        self.task_info = {}
        self.asset_info = {}
        self.upload_info = {}

    @staticmethod
    def check_path(tmp_path):
        """Check if the path exists."""
        if not os.path.exists(tmp_path):
            raise CGFileNotExistsError("{} is not found".format(tmp_path))

    def add_tip(self, code, info):
        """Add error message.

        Args:
            code (str): error code.
            info (str or list): Error message description.

        """
        if isinstance(info, str):
            self.tips_info[code] = [info]
        elif isinstance(info, list):
            self.tips_info[code] = info
        else:
            raise Exception("info must a list or str.")

    def save_tips(self):
        """Write the error message to tips.json."""
        utils.json_save(self.tips_json, self.tips_info, ensure_ascii=False)

    @staticmethod
    def get_current_id():
        if isinstance(threading.current_thread(), threading._MainThread):
            return os.getpid()
        else:
            return threading.get_ident()

    @staticmethod
    def check_local_os(local_os):
        """Check the system name.

        Args:
            local_os (str): System name.

        Returns:
            str

        """
        if not local_os:
            if "win" in sys.platform.lower():
                local_os = "windows"
            else:
                local_os = "linux"
        return local_os

    def check_workspace(self, workspace):
        """Check the working environment.

        Args:
            workspace (str):  Workspace path.

        Returns:
            str: Workspace path.

        """
        if not workspace:
            if self.local_os == "windows":
                workspace = os.path.join(os.environ["USERPROFILE"], "renderfarm_sdk")
            else:
                workspace = os.path.join(os.environ["HOME"], "renderfarm_sdk")
        else:
            self.check_path(workspace)

        return workspace

    def find_location(self):
        """Get the path where the local Unreal Engine startup file is located.

        Raises:
            CGExeNotExistError: The path to the startup file does not exist.

        """
        exe_path = None
        if self.local_os == 'windows':
            for root, dirs, files in os.walk(self.software_install_dir):
                for filename in files:
                    if filename.lower() == "unrealeditor-cmd.exe":
                        exe_path = os.path.normpath(os.path.join(root, filename))
        else:
            exe_path = None

        if exe_path is None or not os.path.exists(exe_path):
            raise CGExeNotExistError(ERROR9899_CGEXE_NOTEXIST.format(self.render_software))

        self.logger.info("exe_path: %s", exe_path)
        return exe_path

    def analyse_cg_file(self):
        """Analyse cg file.

        Analyze the scene file to get the path to the startup file of the CG software.

        """
        if self.custom_exe_path is not None:
            exe_path = self.custom_exe_path
        else:
            exe_path = self.find_location()
        return exe_path

    def write_task_json(self):
        """Initialize task.json."""
        constants.TASK_INFO["task_info"]["input_cg_file"] = self.cg_file.replace("\\", "/")
        constants.TASK_INFO["task_info"]["project_name"] = self.project_name
        constants.TASK_INFO["task_info"]["cg_id"] = constants.CG_SETTING.get(
            self.render_software.capitalize())
        constants.TASK_INFO["task_info"]["os_name"] = "1" if self.local_os == "windows" else "0"
        constants.TASK_INFO["task_info"]["platform"] = self.platform
        constants.TASK_INFO["software_config"] = {
            "plugins": self.plugin_config,
            "cg_version": self.software_version,
            "cg_name": self.render_software,
            "cg_inst_dir": self.software_install_dir
        }
        utils.json_save(self.task_json, constants.TASK_INFO)

    def check_result(self):
        """Check that the analysis results file exists."""
        for json_path in [self.task_json, self.asset_json,
                          self.tips_json]:
            if not os.path.exists(json_path):
                msg = "Json file is not generated: {0}".format(json_path)
                return False, msg
        return True, None

    def get_file_md5(self, file_path):
        """Generate the md5 values for the scenario."""
        hash_md5 = hashlib.md5()
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file_path_f:
                while True:
                    data_flow = file_path_f.read(8096)
                    if not data_flow:
                        break
                    hash_md5.update(data_flow)
        return hash_md5.hexdigest()

    def write_upload_json(self):
        """Generate the upload.json."""
        assets = self.asset_info["asset"]
        upload_asset = []

        self.upload_info["scene"] = [
            {
                "local": self.cg_file.replace("\\", "/"),
                "server": utils.convert_path(self.cg_file),
                "hash": self.get_file_md5(self.cg_file)
            }
        ]

        for path in assets:
            resources = {}
            local = path.split(" (mtime")[0]
            server = utils.convert_path(local)
            resources["local"] = local.replace("\\", "/")
            resources["server"] = server
            upload_asset.append(resources)

        # Add the cg file to upload.json
        upload_asset.append({
            "local": self.cg_file.replace("\\", "/"),
            "server": utils.convert_path(self.cg_file)
        })

        self.upload_info["asset"] = upload_asset

        utils.json_save(self.upload_json, self.upload_info)

    def analyse(self, no_upload=False, exe_path=""):
        """Build a cmd command to perform an analysis scenario.

        Args:
            no_upload (bool): Do you not generate an upload,json file.

        Raises:
            AnalyseFailError: Analysis scenario failed.

        """
        if not os.path.exists(exe_path):
            exe_path = self.analyse_cg_file()
        self.write_task_json()

        analyse_script_name = "Analyze"
        script_path = os.path.normpath(os.path.dirname(__file__)).replace('\\', '/')

        if self.local_os == 'windows':
            analyse_cmd = ('"{exe_path}" "{cg_file}" -run=pythonscript -script="'
                           'import sys;sys.path.insert(0, \'{script_path}\');'
                           'import {analyse_script_name};import importlib;importlib.reload({analyse_script_name});'
                           'Analyze.run(\'{task_json_path}\')"').format(
                exe_path = exe_path,
                cg_file = self.cg_file,
                script_path = script_path,
                analyse_script_name=analyse_script_name,
                task_json_path = os.path.dirname(self.task_json).replace('\\', '/')
            )
        else:
            sys.exit(555)

        self.logger.debug(analyse_cmd)
        code, _, _ = Cmd.run(analyse_cmd, shell=True)
        self.logger.info('return code: {}'.format(code))
        if code != 0:
            self.add_tip(tips_code.UNKNOW_ERR, "")
            self.save_tips()
            raise AnalyseFailError

        # Determine whether the analysis is successful by
        #  determining whether a json file is generated.
        status, msg = self.check_result()
        if status is False:
            self.add_tip(tips_code.UNKNOW_ERR, msg)
            self.save_tips()
            raise AnalyseFailError(msg)

        self.tips_info = utils.json_load(self.tips_json)
        self.asset_info = utils.json_load(self.asset_json)
        self.task_info = utils.json_load(self.task_json)
        if not no_upload:
            self.write_upload_json()
