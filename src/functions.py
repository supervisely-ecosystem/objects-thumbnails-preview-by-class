import numpy as np
import globals as g
import supervisely_lib as sly
from create_gallery import Gallery


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

    selected_classes_names = []
    classes_json = g.meta.obj_classes.to_json()
    for obj_class in classes_json[:]:
        if class_images[obj_class["title"]] == 0:
            classes_json.remove(obj_class)
            continue
        selected_classes_names.append(obj_class["title"])
        obj_class["objectsCount"] = class_objects[obj_class["title"]]
        obj_class["imagesCount"] = class_images[obj_class["title"]]
        obj_class["objectsTotalArea"] = class_objects_total_area[obj_class["title"]]

    data_stats = {"project": [total_images, total_objects], "dataset": [total_ds_images, total_ds_objects]}
    return classes_json, selected_classes_names, len(classes_json) * [True], data_stats


def generate_col_map(class_names):
    col_map = {}
    class_names = list(set(class_names))
    for idx, class_name in enumerate(class_names, start=1):
        col_map[class_name] = idx
    return col_map


def unpack_data(curr_page_data):
    page_data = []
    class_names = []
    for object in curr_page_data:
        for class_name, class_data in object.items():
            class_names.append(class_name)
            page_data.extend(class_data)
    col_map = generate_col_map(class_names)
    return page_data, col_map,


def get_ann_by_image_id(dataset_id, image_ids, batch_cnt):
    batch_name = f"batch_{dataset_id}_{batch_cnt}"
    if g.cache.get(batch_name) is None:
        ann_infos = g.api.annotation.download_batch(dataset_id, image_ids)
        annotations = [sly.Annotation.from_json(ann_info.annotation, g.meta) for ann_info in ann_infos]
        g.cache.add(batch_name, annotations, expire=g.cache_item_expire_time)
    else:
        annotations = g.cache.get(batch_name)
    return annotations


def build_pages_from_page_batches(class_by_page_map, total_pages, progress):
    complete_map = {}
    progress.set_total(total_pages)
    for page in range(1, total_pages + 1):
        complete_map[page] = []
        for class_name, data_by_page in class_by_page_map.items():
            if page > len(data_by_page):
                continue
            complete_map[page].append({class_name: data_by_page[page - 1]})
            if len(complete_map[page]) >= 10:
                break
        progress.increment(1)
    progress.reset_and_update()
    return complete_map


def gen_list_of_lists(original_list, new_structure):
    assert len(original_list) == sum(new_structure), \
        "The number of elements in the original list and desired structure don't match"
    list_of_lists = [[original_list[i + sum(new_structure[:j])] for i in range(new_structure[j])] \
                     for j in range(len(new_structure))]
    return list_of_lists


def get_gallery_map(anns, curr_images_urls, selected_classes):
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


def get_class_by_page_map(gallery_map, objs_per_cls_per_page):
    class_by_page_map = {}
    max_pages = 0
    for class_name, class_objects in gallery_map.items():
        class_by_page_map[class_name] = []
        times = len(class_objects) // objs_per_cls_per_page
        last_digit = len(class_objects) % objs_per_cls_per_page
        if last_digit == 0:
            list_struct = [*np.repeat(objs_per_cls_per_page, times)]
        else:
            list_struct = [*np.repeat(objs_per_cls_per_page, times), last_digit]
        if len(list_struct) > max_pages:
            max_pages = len(list_struct)
        page_objects = gen_list_of_lists(class_objects, list_struct)
        class_by_page_map[class_name].extend(page_objects)
    return class_by_page_map


def get_page_to_obj_class_map(anns, curr_images_urls, selected_classes, app_state, progress):
    g.api.task.set_field(g.TASK_ID, "state.done3", False)
    objs_per_cls_per_page = app_state["objectsPerClassPerPage"]
    g.obj_per_class_per_page = objs_per_cls_per_page

    gallery_map = get_gallery_map(anns, curr_images_urls, selected_classes)
    class_by_page_map = get_class_by_page_map(gallery_map, objs_per_cls_per_page)

    total_pages = 0
    for class_name, arr in gallery_map.items():
        new_arr = list(sly.batched(arr, objs_per_cls_per_page))
        gallery_map[class_name] = new_arr
        total_pages = max(len(new_arr), total_pages)

    page_to_obj_class_map = build_pages_from_page_batches(class_by_page_map, total_pages, progress)
    g.api.task.set_field(g.TASK_ID, "state.done3", True)
    return page_to_obj_class_map, total_pages


def update_gallery_by_page(current_page, state, progress, page_cache):
    selected_classes = state["selectedClasses"]
    g.selected_classes = selected_classes

    if page_cache is None or g.obj_per_class_per_page != state["objectsPerClassPerPage"]:
        page_to_obj_class_map, total_pages = get_page_to_obj_class_map(g.annotations, g.images_urls, selected_classes, state, progress)
        g.page_cache = (page_to_obj_class_map, total_pages)
    else:
        page_to_obj_class_map, total_pages = page_cache
    curr_page_data = page_to_obj_class_map[current_page]

    curr_page_data, col_map = unpack_data(curr_page_data)
    cols = len(col_map)

    full_gallery = Gallery(g.TASK_ID, g.api, 'data.perClass', g.meta, cols, True, True)
    for image_url, ann, image_title in curr_page_data:
        full_gallery.add_item(title=image_title, ann=ann, image_url=image_url,
                              col_index=col_map[ann.labels[0].obj_class.name])
    full_gallery.update(options=True, need_zoom=True)

    fields = [
        {"field": "state.galleryPage", "payload": current_page},
        {"field": "state.totalPages", "payload": total_pages},
        {"field": "state.inputPage", "payload": current_page},
        {"field": "state.loadingGallery", "payload": False}
    ]
    g.api.app.set_fields(g.TASK_ID, fields)
