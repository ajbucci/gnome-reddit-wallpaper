import argparse

from wallgarden.core import Timeframe, Sort, set_gnome_background, get_random_reddit_image

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
