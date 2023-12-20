import argparse
import os
import random
import subprocess  # nosec B404
from enum import Enum
from io import BytesIO

import requests
from PIL import Image

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
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


def download_json(subreddit, sort, timeframe, limit):
    url = f"http://reddit.com/r/{subreddit}/{sort}.json?t={timeframe}&limit={limit}"
    response = requests.get(url, headers=headers, timeout=10)
    return response.json()


def parse_json(data, target_resolution):
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


def positive_integer(value):
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a valid integer")

    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return ivalue


def parse_arguments():
    parser = argparse.ArgumentParser(description="Download, process, and set a desktop background from Reddit.")
    parser.add_argument("subreddit", type=str, help="Subreddit name (default: earthporn)")
    parser.add_argument("--sort", "-s", type=str, choices=[sort.value for sort in Sort], default="hot", help="Sort method (default: top)")
    parser.add_argument(
        "--timeframe", "-t", type=str, choices=[timeframe.value for timeframe in Timeframe], default="day", help="Timeframe (default: day)"
    )
    parser.add_argument("--limit", "-l", type=positive_integer, default=10, help="Positive integer for the limit of posts to fetch (default: 10)")
    return parser.parse_args()


def get_random_reddit_image(subreddit, sort, timeframe, limit, target_resolution):
    image_folder = os.path.join(os.getcwd(), "images")
    json_data = download_json(subreddit, sort, timeframe, limit)
    filtered_images = parse_json(json_data, target_resolution)

    if filtered_images:
        selected_url = random.choice(list(filtered_images.keys()))  # nosec B311
        _, _, title = filtered_images[selected_url]
        # Format and sanitize the title for filename
        safe_title = "".join(c for c in title if c.isalnum() or c in [" ", "-", "_"]).rstrip()
        image_path = os.path.join(image_folder, f"{safe_title}.png")
        image_path_original = os.path.join(image_folder, "originals", f"{safe_title}.original.png")
        # Check if image already exists
        if not os.path.exists(image_path):
            image = download_image(selected_url)
            image.save(image_path_original, "PNG")
            final_image = scale_and_crop(image, target_resolution)
            final_image.save(image_path, "PNG")
        else:
            print(f"Image '{image_path}' already exists.")

    return image_path


def main():
    args = parse_arguments()
    subreddit = args.subreddit
    sort = args.sort
    timeframe = args.timeframe
    limit = args.limit
    target_resolution = (2560, 1440)  # 1440p resolution

    image_path = get_random_reddit_image(subreddit, sort, timeframe, limit, target_resolution)
    set_gnome_background(image_path)


if __name__ == "__main__":
    main()
