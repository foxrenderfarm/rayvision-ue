# -*- coding: utf-8 -*-

from rayvision_ue.analyze_ue import AnalyzeUe

analyze_info = {
    "cg_file": "D:/files/CG file/test.uproject",
    "workspace": "c:/workspace",
    "software_version": "5.6.1",
    "project_name": "Project1",
    "plugin_config": {},
    "software_install_dir": "C:/Program Files/Epic Games/UE_5.6"
}

AnalyzeUe(**analyze_info).analyse()
