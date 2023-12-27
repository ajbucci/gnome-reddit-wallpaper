import argparse

from wallgarden.core import Sort, Timeframe, get_random_image, get_random_pinned_image, get_random_reddit_image, set_gnome_background
from wallgarden.slideshow import install_service_files, install_timer_files, toggle_service


def positive_integer(value):
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a valid integer")

    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return ivalue


def handle_download(args):
    subreddit = args.subreddit
    sort = args.sort
    timeframe = args.timeframe
    limit = args.limit
    target_resolution = (2560, 1440)  # Example resolution

    image_path = get_random_reddit_image(subreddit, sort, timeframe, limit, target_resolution)
    set_gnome_background(image_path)


def handle_random(args):
    if args.pinned:
        image_path = get_random_pinned_image()
    else:
        image_path = get_random_image()

    if image_path:
        set_gnome_background(image_path)
    else:
        print("No images available to set as wallpaper.")


def handle_slideshow(args):
    if args.start:
        toggle_service(enable=True)
    if args.stop:
        toggle_service(enable=False)
    if args.pinned:
        install_service_files(pinned=args.pinned)
    if args.timer:
        install_timer_files(minutes=args.timer)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Wallgarden cli -- download and manage reddit images as desktop backgrounds.")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    parser_dl = subparsers.add_parser("download", help="Download a random wallpaper from Reddit.")
    parser_dl.add_argument("subreddit", type=str, help="Subreddit name (default: earthporn)")
    parser_dl.add_argument("--sort", "-s", type=str, choices=[sort.value for sort in Sort], default="hot", help="Sort method (default: hot)")
    parser_dl.add_argument(
        "--timeframe", "-t", type=str, choices=[timeframe.value for timeframe in Timeframe], default="day", help="Timeframe (default: day)"
    )
    parser_dl.add_argument("--limit", "-l", type=positive_integer, default=10, help="Positive integer for the limit of posts to fetch (default: 10)")

    parser_random = subparsers.add_parser("random", help="Set a random wallpaper.")
    parser_random.add_argument("--pinned", action="store_true", help="Choose only from pinned wallpapers")

    parser_slideshow = subparsers.add_parser("slideshow", help="")
    parser_slideshow.add_argument("--start", action="store_true", help="Start the slideshow.")
    parser_slideshow.add_argument("--stop", action="store_true", help="Stop the slideshow.")
    parser_slideshow.add_argument("--timer", type=positive_integer, default=10, help="Set a timer for the wallpaper duration in minutes")
    parser_slideshow.add_argument("--pinned", action="store_true", help="Choose only from pinned wallpapers")

    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()

    if args.command == "download":
        handle_download(args)
    elif args.command == "random":
        handle_random(args)
    elif args.command == "slideshow":
        handle_slideshow(args)
    else:
        print("No valid command provided. Use 'download' to download or 'random' to set a random wallpaper.")


if __name__ == "__main__":
    main()
