import os
import sys
from pathlib import Path

import globals as g
import supervisely as sly


root_source_dir = str(Path(sys.argv[0]).parents[1])
sly.logger.info(f"Root source directory: {root_source_dir}")
sys.path.append(root_source_dir)

source_path = str(Path(sys.argv[0]).parents[0])
sly.logger.info(f"Source directory: {source_path}")
sys.path.append(source_path)

ui_sources_dir = os.path.join(source_path, "ui")
sys.path.append(ui_sources_dir)
sly.logger.info(f"Added to sys.path: {ui_sources_dir}")


import init_ui


def main():
    sly.logger.info("Script arguments", extra={
        "TASK ID": g.TASK_ID,
        "context.teamId": g.TEAM_ID,
        "context.workspaceId": g.WORKSPACE_ID,
        "modal.state.slyProjectId": g.PROJECT_ID
    })

    data = {}
    state = {}

    init_ui.init(data, state)

    g.my_app.compile_template(root_source_dir)
    g.my_app.run(state=state, data=data)


if __name__ == "__main__":
    sly.main_wrapper("main", main)
