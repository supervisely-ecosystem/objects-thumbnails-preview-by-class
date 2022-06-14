import globals as g
import functions as f
import supervisely as sly

progress1 = sly.app.widgets.ProgressBar(g.TASK_ID, g.api, "data.progress1", "Download annotations", min_report_percent=5)


def init(data, state, stats):
    data["projectId"] = g.project_info.id
    data["projectName"] = g.project_info.name
    data["projectPreviewUrl"] = g.api.image.preview_url(g.project_info.reference_image_url, 100, 100)
    data["projectTotalImages"] = stats["project"][0]
    data["projectTotalObjects"] = stats["project"][1]
    if g.DATASET_ID is not None:
        data["datasetId"] = g.dataset_info.id
        data["datasetName"] = g.dataset_info.name
        data["datasetPreviewUrl"] = g.api.image.preview_url(g.dataset_preview_image.full_storage_url, 100, 100)
        data["previewImageId"] = g.dataset_preview_image.id
        data["datasetTotalImages"] = stats["dataset"][0]
        data["datasetTotalObjects"] = stats["dataset"][1]

    data["done1"] = False
    progress1.init_data(data)

    state["teamId"] = g.TEAM_ID
    state["workspaceId"] = g.WORKSPACE_ID

    state["activeStep"] = 1
    state["collapsed1"] = False


@g.my_app.callback("download-annotations")
@sly.timeit
@g.my_app.ignore_errors_and_show_dialog_window()
def download_annotations(api: sly.Api, task_id, context, state, app_logger):
    if g.DATASET_ID is not None:
        progress1.set_total(g.dataset_info.items_count)
    else:
        progress1.set_total(g.project_info.items_count)

    batch_cnt = 0
    for dataset in g.datasets:
        images = api.image.get_list(dataset.id, sort="name")
        image_ids = [image_info.id for image_info in images]
        g.image_ids.extend(image_ids)
        g.images_urls.extend([image_info.path_original for image_info in images])
        for batch in sly.batched(image_ids):
            batch_cnt += 1
            g.annotations.extend(f.get_ann_by_image_id(dataset.id, batch, batch_cnt))
            progress1.increment(len(batch))

    progress1.reset_and_update()

    fields = [
        {"field": "data.done1", "payload": True},
        {"field": "state.collapsed2", "payload": False},
        {"field": "state.disabled2", "payload": False},
        {"field": "state.activeStep", "payload": 2},
    ]
    g.api.app.set_fields(g.TASK_ID, fields)
