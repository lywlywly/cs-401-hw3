import importlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from time import sleep, time

from redis import Redis


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_INPUT_KEY = os.getenv("REDIS_INPUT_KEY", "metrics")
REDIS_OUTPUT_KEY = os.getenv("REDIS_OUTPUT_KEY", "lw337-proj3-output")

FUNCTION_PATH = os.getenv("FUNCTION_PATH")

FUNCTION_ZIP_PATH = os.getenv("FUNCTION_ZIP_PATH")
ZIPPED_MODULE_NAME = os.getenv("ZIPPED_MODULE_NAME")

HANDLER_FUNCTION_NAME = os.getenv("HANDLER_FUNCTION_NAME", "handler")

INTERVAL_SECONDS = float(os.getenv("INTERVAL_SECONDS", "5.0"))


def load_py_file(py_file_path, entry_function_name):
    sys.path.insert(0, os.path.dirname(py_file_path))
    module = importlib.import_module(os.path.basename(py_file_path)[:-3])

    return getattr(module, entry_function_name)


def load_zip_file(zip_file_path, module_name, entry_function_name):
    sys.path.insert(0, zip_file_path)
    print(os.listdir("/opt/function_module/"))

    import zipfile

    zip_file_path = "/opt/function_module/module.zip"

    with zipfile.ZipFile(zip_file_path, "r") as zip_file:
        contents = zip_file.namelist()

        for item in contents:
            print(item)

    print(module_name)
    module = importlib.import_module(module_name)

    print(dir(module))
    return getattr(module, entry_function_name)


def get_entry_function_and_mtime():
    if FUNCTION_ZIP_PATH:
        function = load_zip_file(
            FUNCTION_ZIP_PATH, ZIPPED_MODULE_NAME, HANDLER_FUNCTION_NAME
        )
        mtime = os.path.getmtime(FUNCTION_ZIP_PATH)
    else:
        function = load_py_file(FUNCTION_PATH, HANDLER_FUNCTION_NAME)
        mtime = os.path.getmtime(FUNCTION_PATH)

    return function, mtime


@dataclass()
class Context:
    host: str
    port: int
    input_key: str
    output_key: str
    function_getmtime: datetime
    last_execution: datetime
    env: dict


def main():
    function, mtime = get_entry_function_and_mtime()

    context = Context(
        host=REDIS_HOST,
        port=REDIS_PORT,
        input_key=REDIS_INPUT_KEY,
        output_key=REDIS_OUTPUT_KEY,
        function_getmtime=mtime,
        last_execution=None,
        env={},
    )
    redis = Redis(host=REDIS_HOST, port=REDIS_PORT)

    while True:
        metrics = json.loads(redis.get(REDIS_INPUT_KEY))
        result = function(metrics, context)
        context.last_execution = time()
        redis.set(REDIS_OUTPUT_KEY, json.dumps(result))
        sleep(INTERVAL_SECONDS)


main() if __name__ == "__main__" else None
