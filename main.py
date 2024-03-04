import importlib
import sys

sys.path.insert(0, "serverless_function.zip")
print(sys.path)
import zipfile

with zipfile.ZipFile("serverless_function.zip", "r") as zip_file:
    contents = zip_file.namelist()

    for item in contents:
        print(item)

m = importlib.import_module("serverless_function.handle")

print(dir(m))
