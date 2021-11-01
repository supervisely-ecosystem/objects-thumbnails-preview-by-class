import os
import globals as g
import supervisely_lib as sly
from create_gallery import Gallery
from supervisely_lib.io.json import dump_json_file
from supervisely_lib.io.fs import silent_remove, get_file_name

#from supervisely_lib.app.widgets.create_gallery import Gallery


def get_ann_by_id(image_id, save_path):
    if g.cache.get(image_id) is None:
        ann_info = g.api.annotation.download(image_id)
        ann_json = ann_info.annotation
        ann_json_name = get_file_name(ann_info.image_name) + '.json'
        ann_json_path = os.path.join(save_path, ann_json_name)
        dump_json_file(ann_json, ann_json_path)
        g.cache.add(image_id, ann_json, expire=g.cache_item_expire_time)
        silent_remove(ann_json_path)
    else:
        ann_json = g.cache.get(image_id)
    ann = sly.Annotation.from_json(ann_json, g.meta)
    return ann


def unpack_gallery_map(gallery_map, selected_classes):
    title_names = []
    anns = []
    ann_label_names = []
    images_urls = []
    cols_map = {}
    col_id = 1
    for idx, obj_class_name in enumerate(selected_classes, start=1):
        obj_cnt = 1
        cols_map[obj_class_name] = col_id
        col_id += 1
        if col_id > 10:
            col_id = 1
        for image_url, ann in gallery_map[obj_class_name]:
            title_names.append(f"{obj_class_name}_{obj_cnt}")
            obj_cnt += 1
            ann_label_names.append(obj_class_name)
            anns.append(ann)
            images_urls.append(image_url)
    return title_names, anns, ann_label_names, images_urls, cols_map


def labels_to_anns(anns, curr_images_urls, selected_classes):
    gallery_map = {}
    for obj_class_name in selected_classes:
        gallery_map[obj_class_name] = []
        for ann, image_url in zip(anns, curr_images_urls):
            for label in ann.labels:
                if label.obj_class.name != obj_class_name:
                    continue
                new_ann = ann.clone(labels=[label])
                gallery_map[obj_class_name].append((image_url, new_ann))

    title_names, anns, ann_label_names, images_urls, cols_map = unpack_gallery_map(gallery_map, selected_classes)
    return title_names, anns, ann_label_names, images_urls, cols_map


def update_gallery_by_page(current_page, state, selected_classes):
    g.selected_classes = selected_classes
    cols = len(selected_classes)
    if len(selected_classes) > 10:
        cols = 10

    images_per_page = state['rows']

    curr_anns = [get_ann_by_id(image_id, g.cache_dir) for image_id in g.image_ids]
    curr_images_names, curr_anns, cur_ann_label_names, curr_images_urls, cols_map = labels_to_anns(curr_anns, g.images_urls, selected_classes)

    page_images_names = curr_images_names[images_per_page * (current_page - 1):images_per_page * current_page]
    page_anns = curr_anns[images_per_page * (current_page - 1):images_per_page * current_page]
    page_anns_label_names = cur_ann_label_names[images_per_page * (current_page - 1):images_per_page * current_page]
    page_images_urls = curr_images_urls[images_per_page * (current_page - 1):images_per_page * current_page]

    if len(page_anns_label_names) < cols:
        page_anns_label_names = set(page_anns_label_names)
        cols = len(page_anns_label_names)
        cols_map = {}
        for idx, obj_class_name in enumerate(page_anns_label_names, start=1):
            cols_map[obj_class_name] = idx

    full_gallery = Gallery(g.TASK_ID, g.api, 'data.perClass', g.meta, cols, True, True)

    for idx, (image_name, ann, obj_class_name, image_url) in enumerate(zip(page_images_names, page_anns, page_anns_label_names, page_images_urls)):
        col_idx = cols_map[obj_class_name]
        #if col_idx > 10:
        #    continue
        full_gallery.add_item(title=image_name, ann=ann, image_url=image_url, col_index=col_idx)
    full_gallery.update(options=True, need_zoom=True)

    max_pages_count = len(curr_images_names) // images_per_page
    if len(curr_images_names) % images_per_page != 0:
        max_pages_count += 1

    fields = [
        {"field": "state.galleryPage", "payload": current_page},
        {"field": "state.galleryMaxPage", "payload": max_pages_count},
        {"field": "state.input", "payload": current_page},
        {"field": "state.maxImages", "payload": len(curr_images_names)},
        {"field": "state.rows", "payload": images_per_page},
        {"field": "state.cols", "payload": cols},
        {"field": "state.with_info", "payload": True}
    ]
    g.api.app.set_fields(g.TASK_ID, fields)
