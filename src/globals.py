import os
from diskcache import Cache
import supervisely_lib as sly
from supervisely_lib.io.fs import mkdir

my_app = sly.AppService()
api: sly.Api = my_app.public_api

TASK_ID = my_app.task_id
TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])
PROJECT_ID = int(os.environ['modal.state.slyProjectId'])
DATASET_ID = os.environ.get('modal.state.slyDatasetId', None)
if DATASET_ID is not None:
    DATASET_ID = int(DATASET_ID)

project_info = api.project.get_info_by_id(PROJECT_ID)
meta_json = api.project.get_meta(project_info.id)
meta = sly.ProjectMeta.from_json(meta_json)

if DATASET_ID is not None:
    dataset_info = api.dataset.get_info_by_id(DATASET_ID)
    datasets = [dataset_info]
    images = api.image.get_list(dataset_info.id, sort="name")
else:
    datasets = api.dataset.get_list(PROJECT_ID)
    images = []
    for dataset in datasets:
        ds_images = api.image.get_list(dataset.id, sort="name")
        images.extend(ds_images)

image_ids = []
images_urls = []

work_dir = os.path.join(my_app.data_dir, "work_dir")
mkdir(work_dir, True)
cache_dir = os.path.join(my_app.cache_dir, "diskcache")
mkdir(cache_dir)
cache = Cache(directory=cache_dir)
cache_item_expire_time = 600  # seconds

annotations = []
selected_classes = []

page_cache = None
obj_per_class_per_page = None

first_page = 1
old_input = None
