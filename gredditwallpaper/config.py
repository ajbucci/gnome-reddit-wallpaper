import os

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_NAME = os.path.basename(PROJECT_PATH)

DATA_DIR_PATH = os.path.expanduser("~/.local/share/" + PROJECT_NAME)
IMAGE_DIR_NAME = "images"
ORIGINAL_IMAGE_DIR_NAME = "original_images"
IMAGE_DIR_PATH = os.path.join(DATA_DIR_PATH, IMAGE_DIR_NAME)
ORIGINAL_IMAGE_DIR_PATH = os.path.join(DATA_DIR_PATH, ORIGINAL_IMAGE_DIR_NAME)

if not os.path.exists(IMAGE_DIR_PATH):
    os.makedirs(IMAGE_DIR_PATH)

if not os.path.exists(ORIGINAL_IMAGE_DIR_PATH):
    os.makedirs(ORIGINAL_IMAGE_DIR_PATH)
