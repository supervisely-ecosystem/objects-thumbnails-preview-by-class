import init_ui
import globals as g
import functions as f
import supervisely_lib as sly
import classes_table


@g.my_app.callback("init-gallery")
@sly.timeit
def init_gallery(api: sly.Api, task_id, context, state, app_logger):
    current_page = state['galleryPage']
    f.update_gallery_by_page(current_page, state, state["selectedClasses"])


@g.my_app.callback("update-gallery")
@sly.timeit
def update_gallery(api: sly.Api, task_id, context, state, app_logger):
    g.old_input = state['galleryPage']
    go_to_page = state.get('inputPage')
    current_page = int(go_to_page)
    if g.old_input > current_page or g.selected_classes != state['selectedClasses']:
        current_page = g.first_page
    g.old_rows = state['rows']
    f.update_gallery_by_page(current_page, state, state["selectedClasses"])


def main():
    sly.logger.info("Script arguments", extra={
        "TASK ID": g.TASK_ID,
        "context.teamId": g.TEAM_ID,
        "context.workspaceId": g.WORKSPACE_ID,
        "modal.state.slyProjectId": g.PROJECT_ID
    })

    data = {}
    state = {}

    classes_json, selected_classes_names, selected_classes, stats = classes_table.build(g.api, g.PROJECT_ID, g.meta, g.DATASET_ID)
    init_ui.init(data, state, classes_json, selected_classes_names, selected_classes, stats)

    g.my_app.run(state=state, data=data, initial_events=[{"state": state, "command": "init-gallery"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
