# Gnome Reddit Wallpaper
Download and set a desktop background using a random image from a chosen subreddit via CLI or GUI.

![screenshot](https://raw.githubusercontent.com/ajbucci/gnome-reddit-wallpaper/main/gredditwallpaper.png)
## CLI
```
positional arguments:
  subreddit             Subreddit name (default: earthporn)

options:
  -h, --help            show this help message and exit
  --sort {hot,new,rising,controversial,top,best}, -s {hot,new,rising,controversial,top,best}
                        Sort method (default: top)
  --timeframe {all,day,hour,month,week,year}, -t {all,day,hour,month,week,year}
                        Timeframe (default: day)
  --limit LIMIT, -l LIMIT
                        Positive integer for the limit of posts to fetch (default: 10)
```
## TODO
- [ ] add build instructions
- [ ] add tests
- [ ] add documentation
- [ ] allow user to delete wallpapers with the GUI
- [ ] allow users to adjust the image cropping with the GUI
