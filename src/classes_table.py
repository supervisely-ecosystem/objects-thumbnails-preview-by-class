import supervisely_lib as sly


def build(api: sly.Api, project_id, project_meta: sly.ProjectMeta, dataset_id=None):
    stats = api.project.get_stats(project_id)

    total_images = stats["images"]["total"]["imagesInDataset"]
    total_ds_images = stats["datasets"]["total"]["imagesCount"]

    class_images = {}
    for item in stats["images"]["objectClasses"]:
        if dataset_id is None:
            class_images[item["objectClass"]["name"]] = item["total"]
        else:
            for ds in item["datasets"]:
                if ds["id"] == dataset_id:
                    class_images[item["objectClass"]["name"]] = ds["count"]

    class_objects = {}
    total_objects = 0
    total_ds_objects = 0
    for item in stats["objects"]["items"]:
        total_objects += item["total"]
        if dataset_id is None:
            class_objects[item["objectClass"]["name"]] = item["total"]
        else:
            for ds in item["datasets"]:
                if ds["id"] == dataset_id:
                    class_objects[item["objectClass"]["name"]] = ds["count"]
                    total_ds_objects += ds["count"]

    class_objects_total_area = {}
    for item in stats["objectsArea"]["items"]:
        if dataset_id is None:
            class_objects_total_area[item["objectClass"]["name"]] = f"{round(item['total'], 2)}%"
        else:
            for ds in item["datasets"]:
                if ds["id"] == dataset_id:
                    class_objects_total_area[item["objectClass"]["name"]] = f"{round(ds['percentage'], 2)}%"

    selected_classes_names = []
    classes_json = project_meta.obj_classes.to_json()
    for obj_class in classes_json[:]:
        if class_images[obj_class["title"]] == 0:
            classes_json.remove(obj_class)
            continue
        selected_classes_names.append(obj_class["title"])
        obj_class["objectsCount"] = class_objects[obj_class["title"]]
        obj_class["imagesCount"] = class_images[obj_class["title"]]
        obj_class["objectsTotalArea"] = class_objects_total_area[obj_class["title"]]

    stats = {"project": [total_images, total_objects], "dataset": [total_ds_images, total_ds_objects]}
    return classes_json, selected_classes_names, len(classes_json) * [True], stats
