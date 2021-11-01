import globals as g


def init(data, state, classes_json, selected_classes_names, selected_classes, stats):
    data["classes"] = classes_json
    data["projectId"] = g.project_info.id
    data["projectName"] = g.project_info.name
    data["projectPreviewUrl"] = g.api.image.preview_url(g.project_info.reference_image_url, 100, 100)
    data["projectTotalImages"] = stats["project"][0]
    data["projectTotalObjects"] = stats["project"][1]
    if g.DATASET_ID is not None:
        data["datasetId"] = g.dataset_info.id
        data["datasetName"] = g.dataset_info.name
        data["datasetPreviewUrl"] = g.api.image.preview_url(g.dataset_info.reference_image_url, 100, 100)
        data["datasetTotalImages"] = stats["dataset"][0]
        data["datasetTotalObjects"] = stats["dataset"][1]
    data["perClass"] = None

    state["selectedClasses"] = selected_classes_names
    state["classes"] = selected_classes
    state["rows"] = 100  # max images per page
    # state["rows"] = state["cols"] * 20  # max images per page
    state["datasets"] = g.datasets
    state["with_info"] = True
    state["inputPage"] = 1
    state["maxImages"] = None
    state["galleryPage"] = 1
    if g.DATASET_ID is None:
        state["galleryMaxPage"] = data["projectTotalObjects"] // state["rows"]
        if data["projectTotalObjects"] % state["rows"] != 0:
            state["galleryMaxPage"] += 1
    else:
        state["galleryMaxPage"] = data["datasetTotalObjects"] // state["rows"]
        if data["datasetTotalObjects"] % state["rows"] != 0:
            state["galleryMaxPage"] += 1
