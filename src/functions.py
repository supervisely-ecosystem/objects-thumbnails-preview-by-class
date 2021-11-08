import globals as g
import supervisely_lib as sly
from supervisely_lib.app.widgets.grid_gallery import Gallery


def get_input_data_and_classes_stats(project_id, dataset_id=None):
    stats = g.api.project.get_stats(project_id)

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

    table_meta = g.meta
    for obj_class in table_meta.obj_classes:
        if obj_class.geometry_type == sly.Cuboid or obj_class.geometry_type == sly.Point or obj_class.geometry_type == sly.Polyline:
            table_meta = table_meta.delete_obj_class(obj_class.name)

    classes_json = table_meta.obj_classes.to_json()
    for obj_class in classes_json[:]:
        if class_images[obj_class["title"]] == 0:
            classes_json.remove(obj_class)
            continue
        obj_class["objectsCount"] = class_objects[obj_class["title"]]
        obj_class["imagesCount"] = class_images[obj_class["title"]]
        obj_class["objectsTotalArea"] = class_objects_total_area[obj_class["title"]]

    data_stats = {"project": [total_images, total_objects], "dataset": [total_ds_images, total_ds_objects]}
    return classes_json, data_stats


def generate_col_map(curr_page_data):
    class_names = []
    for image_url, ann, obj_name, col_idx in curr_page_data:
        class_names.append(ann.labels[0].obj_class.name)
    col_map = {}
    class_names = list(set(class_names))
    for idx, class_name in enumerate(class_names, start=1):
        col_map[class_name] = idx
    return col_map


def get_ann_by_image_id(dataset_id, image_ids, batch_cnt):
    batch_name = f"batch_{dataset_id}_{batch_cnt}"
    if g.cache.get(batch_name) is None:
        ann_infos = g.api.annotation.download_batch(dataset_id, image_ids)
        annotations = [sly.Annotation.from_json(ann_info.annotation, g.meta) for ann_info in ann_infos]
        g.cache.add(batch_name, annotations, expire=g.cache_item_expire_time)
    else:
        annotations = g.cache.get(batch_name)
    return annotations


def build_gallery_map(anns, curr_images_urls, selected_classes):
    gallery_map = {}
    for obj_class_name in selected_classes:
        curr_cls_objs = []
        gallery_map[obj_class_name] = curr_cls_objs
        for ann, image_url in zip(anns, curr_images_urls):
            for label in ann.labels:
                if label.obj_class.name != obj_class_name:
                    continue
                new_ann = ann.clone(labels=[label])
                image_title = f"{obj_class_name}_{len(curr_cls_objs) + 1}"
                curr_cls_objs.append((image_url, new_ann, image_title))
    return gallery_map


def build_pages(gallery_map, app_state):
    pages = []
    for class_name, arr in gallery_map.items():
        gallery_map[class_name] = list(reversed(arr))

    cur_page_batch = []
    cls_per_page = 10
    objs_per_cls = app_state["objectsPerClassPerPage"]
    items_list = list(gallery_map.items())
    while len(items_list) > 0:
        for col_idx, (class_name, class_objs) in enumerate(items_list[:cls_per_page]):
            cur_page_batch += [obj + tuple([col_idx + 1]) for obj in
                               class_objs[-objs_per_cls:]]
            del class_objs[-objs_per_cls:]

            if len(class_objs) == 0:
                del gallery_map[class_name]

        if len(cur_page_batch) > 0:
            pages.append(cur_page_batch)
            cur_page_batch = []

        items_list = list(gallery_map.items())
    return pages


def get_pages(anns, curr_images_urls, selected_classes, app_state):
    objs_per_cls_per_page = app_state["objectsPerClassPerPage"]
    g.obj_per_class_per_page = objs_per_cls_per_page

    gallery_map = build_gallery_map(anns, curr_images_urls, selected_classes)
    pages = build_pages(gallery_map, app_state)
    return pages


def update_gallery_by_page(current_page, state, page_cache):
    selected_classes = state["selectedClasses"]
    g.selected_classes = selected_classes

    if page_cache is None:
        pages = get_pages(g.annotations, g.images_urls, selected_classes, state)
        g.page_cache = (pages)
    else:
        pages = page_cache
    curr_page_data = pages[current_page - 1]

    col_map = generate_col_map(curr_page_data)
    cols = len(col_map.items())

    full_gallery = Gallery(g.TASK_ID, g.api, 'data.perClass', g.meta, cols, resize_on_zoom=True, show_preview=True)
    for image_url, ann, image_title, col_idx in curr_page_data:
        full_gallery.add_item(title=image_title, ann=ann, image_url=image_url, col_index=col_idx, zoom_to_figure=(ann.labels[0].to_json()["id"], state["zoomFactor"]))
    full_gallery.update(options=True)

    fields = [
        {"field": "state.galleryPage", "payload": current_page},
        {"field": "state.totalPages", "payload": len(pages)},
        {"field": "state.inputPage", "payload": current_page},
        {"field": "state.loadingGallery", "payload": False},
        {"field": "state.done3", "payload": True}
    ]
    g.api.app.set_fields(g.TASK_ID, fields)
