import glob
import os

for item in os.listdir("."):
    if os.path.isfile(os.path.join(".", item)):
        continue

    dir_path = os.path.join(".", item)
    data_dir = os.path.join(dir_path, "data")
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    for dzn in glob.glob(os.path.join(dir_path, "**/*.dzn")):
        os.rename(dzn, os.path.join(data_dir, os.path.basename(dzn)))