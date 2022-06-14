import globals as g
import functions as f
import supervisely as sly


def init(data, state, classes_json):
    data["classes"] = classes_json

    state["loadingGallery"] = True
    state["selectedClasses"] = [] #selected_classes_names
    state["objectsPerClassPerPage"] = 10
    state["zoomFactor"] = 1.2

    state["disabled2"] = True
    state["collapsed2"] = False

    state["disabled3"] = True
    state["collapsed3"] = False

    state["inputPage"] = 1
    state["totalPages"] = 0
    state["galleryPage"] = 1
    state["loadingGallery"] = False

    state["done3"] = True


@g.my_app.callback("update-gallery")
@sly.timeit
def update_gallery(api: sly.Api, task_id, context, state, app_logger):
    fields = [
        {"field": "state.activeStep", "payload": 3},
        {"field": "state.disabled3", "payload": False},
        {"field": "state.loadingGallery", "payload": True},
        {"field": "state.done3", "payload": False}
    ]
    g.api.app.set_fields(g.TASK_ID, fields)

    g.previous_input = state['galleryPage']
    go_to_page = state.get('inputPage')
    current_page = int(go_to_page)
    if g.selected_classes != state['selectedClasses'] or g.obj_per_class_per_page != state["objectsPerClassPerPage"]:
        current_page = 1
        g.page_cache = None
    f.update_gallery_by_page(current_page, state, g.page_cache)
