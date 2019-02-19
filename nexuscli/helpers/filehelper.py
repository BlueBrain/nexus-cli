import os
import json
import glob


def find_all(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in dirs:
            result.append(os.path.join(root, ''))
    return result

def get_files_by_extensions(schemas_dir, extension):
    return glob.glob(schemas_dir + "/**/*" + extension, recursive=True)

def is_file(path):
    return os.path.isfile(path)

def open_as_json(path):

    if not os.path.isdir(path):
        with open(path) as json_file:
            try:
                return json.load(json_file)
            except Exception as e:
                message = """Unable to load the file (%s) as json. Please provide a valid json file: %s""" % (
                path, e)
                raise Exception(message)
            finally:
                json_file.close()
    else:
        message = """Unable to open the dir (%s) as json. Please provide a valid json file.""" % (path)
        raise Exception(message)

