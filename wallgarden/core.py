import json
import os
import random
import re
import subprocess  # nosec B404
from enum import Enum
from io import BytesIO

import requests
from PIL import Image

from wallgarden.config import IMAGE_DIR_PATH, JSON_PATH, ORIGINAL_IMAGE_DIR_PATH


class Timeframe(Enum):
    all = "all"
    day = "day"
    hour = "hour"
    month = "month"
    week = "week"
    year = "year"


class Sort(Enum):
    hot = "hot"
    new = "new"
    rising = "rising"
    controversial = "controversial"
    top = "top"
    best = "best"


DEFAULT_IMAGE_PROPS = {"hidden": False, "pinned": False, "attempt_download": True, "is_set": False}

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


def query_reddit(subreddit, sort, timeframe, limit):
    url = f"http://reddit.com/r/{subreddit}/{sort}.json?t={timeframe}&limit={limit}"
    response = requests.get(url, headers=headers, timeout=10)
    return response.json()


def parse_reddit(data, target_resolution):
    filtered = {}
    for item in data["data"]["children"]:
        img_data = item["data"]
        url = img_data.get("url")
        width = img_data.get("preview", {}).get("images", [{}])[0].get("source", {}).get("width")
        height = img_data.get("preview", {}).get("images", [{}])[0].get("source", {}).get("height")
        permalink = img_data.get("permalink", "")
        title = permalink.rstrip("/").split("/")[-1]  # Extract title from permalink

        if url and width and height and width > target_resolution[0] and height > target_resolution[1]:
            filtered[url] = (width, height, title)
    return filtered


def download_image(url):
    response = requests.get(url, timeout=10)
    return Image.open(BytesIO(response.content))


def scale_and_crop(image, target_resolution):
    img_width, img_height = image.size
    target_width, target_height = target_resolution
    # abort if the image not correct size
    if img_width < target_width or img_height < target_height:
        return None
    # Determine scaling factor
    scale_factor = max(target_width / img_width, target_height / img_height)

    # Scale the image
    new_size = (int(img_width * scale_factor), int(img_height * scale_factor))
    image = image.resize(new_size, Image.Resampling.LANCZOS)

    # Crop the image
    left = (image.width - target_width) / 2
    top = (image.height - target_height) / 2
    right = (image.width + target_width) / 2
    bottom = (image.height + target_height) / 2

    image = image.crop((left, top, right, bottom))
    return image


def set_gnome_background(image_path):
    try:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{image_path}"], check=True)  # nosec B607, B603
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", f"file://{image_path}"], check=True
        )  # nosec B607, B603
    except subprocess.CalledProcessError as e:
        print(f"Error setting GNOME background: {e}")
    else:
        current_image_path = get_current_wallgarden_background()
        if current_image_path:
            update_image_properties(current_image_path, is_set=False)
        update_image_properties(image_path, is_set=True)


def get_random_reddit_image(subreddit, sort, timeframe, limit, target_resolution):
    json_data = query_reddit(subreddit, sort, timeframe, limit)
    filtered_images = parse_reddit(json_data, target_resolution)

    if filtered_images:
        selected_url = random.choice(list(filtered_images.keys()))  # nosec B311
        _, _, title = filtered_images[selected_url]
        # Format and sanitize the title for filename
        safe_title = "".join(c for c in title if c.isalnum() or c in [" ", "-", "_"]).rstrip()
        image_path = os.path.join(IMAGE_DIR_PATH, f"{safe_title}.png")
        image_path_original = os.path.join(ORIGINAL_IMAGE_DIR_PATH, f"{safe_title}.original.png")
        # Check if image already exists
        if not os.path.exists(image_path):
            image = download_image(selected_url)
            image.save(image_path_original, "PNG")
            final_image = scale_and_crop(image, target_resolution)
            if final_image:
                final_image.save(image_path, "PNG")
            else:
                update_image_properties(image_path, fetch=False)
                return None
        else:
            print(f"Image '{image_path}' already exists.")

        return image_path
    return None


def get_current_wallgarden_background():
    image_properties = load_image_properties()
    for image in image_properties:
        if image_properties[image]["is_set"]:
            return image


def get_monitor_resolutions():
    drm_dir = "/sys/class/drm/"

    # Regex to extract resolution
    resolution_pattern = re.compile(r"(\d+)x(\d+)")

    width, height = (0, 0)
    for card in os.listdir(drm_dir):
        modes_path = os.path.join(drm_dir, card, "modes")
        if os.path.exists(modes_path):
            with open(modes_path, "r") as file:
                for mode in file:
                    match = resolution_pattern.match(mode.strip())
                    if match:
                        this_width, this_height = match.groups()
                        this_width = int(this_width)
                        this_height = int(this_height)
                        if this_width * this_height > width * height:
                            width = this_width
                            height = this_height

    return width, height


def update_image_properties(filepath, **properties):
    data = load_image_properties()
    if filepath not in data:
        data[filepath] = DEFAULT_IMAGE_PROPS
    data[filepath].update(properties)
    save_json_data(data)


def init_image_properties():
    data = load_image_properties()

    # Specify the directory where your images are stored
    for filename in os.listdir(IMAGE_DIR_PATH):
        filepath = os.path.join(IMAGE_DIR_PATH, filename)
        if filepath.lower().endswith((".jpg", ".png", ".jpeg")):
            if filepath not in data:
                data[filepath] = DEFAULT_IMAGE_PROPS
            else:
                for prop in DEFAULT_IMAGE_PROPS:
                    if prop not in data[filepath]:
                        data[filepath][prop] = DEFAULT_IMAGE_PROPS[prop]

    save_json_data(data)
    return data


def get_random_image(filter_dict=None):
    if filter_dict is None:
        filter_dict = {"is_set": False}
    images_dict = load_image_properties()
    filtered_list = []
    for image in images_dict:
        image_props = images_dict[image]
        image_props_subset = {k: image_props[k] for k in filter_dict.keys() if k in image_props}
        if image_props_subset == filter_dict:
            filtered_list.append(image)

    return random.choice(filtered_list)  # nosec B311


def get_random_pinned_image():
    return get_random_image(filter_dict={"is_set": False, "pinned": True})


def load_image_properties():
    # Check if the file exists
    if not os.path.exists(JSON_PATH):
        # If not, create an empty JSON file
        with open(JSON_PATH, "w") as file:
            json.dump({}, file)

    # Now, safely load the file
    try:
        with open(JSON_PATH, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        # Handle the case where the file is empty or corrupted
        return {}


def save_json_data(data):
    with open(JSON_PATH, "w") as file:
        json.dump(data, file, indent=4)
