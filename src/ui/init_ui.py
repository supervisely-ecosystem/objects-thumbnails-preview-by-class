import supervisely_lib as sly
import globals as g
import functions as f
import input_data
import class_selector


@sly.timeit
def init(data, state):
    classes_json, data_stats = f.get_input_data_and_classes_stats(g.PROJECT_ID, g.DATASET_ID)

    input_data.init(data, state, data_stats)
    class_selector.init(data, state, classes_json)

