import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, GObject, Gio
import os
from src.gredditwallpaper import Timeframe, Sort, set_gnome_background, get_random_reddit_image

class Thumbnail(GObject.Object):
    def __init__(self, pixbuf, filename):
        super().__init__()
        self.pixbuf = pixbuf
        self.filename = filename

class ThumbnailRow(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.picture = Gtk.Picture()

        self.append(self.picture)
        self.set_vexpand(False)
        self.set_hexpand(False)
        self.width = 200
        # self.set_size_request(160, 90)  # Request a specific size for each thumbnail row

    def set_thumbnail(self, thumbnail):
        pixbuf_ratio = thumbnail.pixbuf.get_height() / thumbnail.pixbuf.get_width()
        height = self.width * pixbuf_ratio
        self.set_size_request(self.width, height)
        self.picture.set_pixbuf(thumbnail.pixbuf)
        texture = Gdk.Texture.new_for_pixbuf(thumbnail.pixbuf)
        self.picture.set_paintable(texture)

class GRedditWallpaperWindow(Gtk.ApplicationWindow):
    def __init__(self, **kargs):
        super().__init__(**kargs, title='GRedditWallpaper')
        box_main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box_main.set_name("box_main")
        self.set_child(box_main)
        self.image_folder = os.path.join(os.getcwd(), "images")
        # ListModel for Thumbnails
        self.thumbnail_model = Gio.ListStore(item_type=Thumbnail)
        self.load_thumbnails()

        # ScrolledWindow for GridView
        scrolled_window = Gtk.ScrolledWindow(vexpand=True)
        
        # GridView for Thumbnails
        self.thumbnail_single_selection = Gtk.SingleSelection.new(model=self.thumbnail_model)
        self.grid_view = Gtk.GridView(model=self.thumbnail_single_selection)
        thumb_factory = Gtk.SignalListItemFactory()
        thumb_factory.connect("setup", self.setup_thumb_factory)
        thumb_factory.connect("bind", self.bind_thumb_factory)
        self.grid_view.set_factory(thumb_factory)
        scrolled_window.set_child(self.grid_view)
        box_main.append(scrolled_window)

        input_box = Gtk.Box(spacing=10)
        box_main.append(input_box)
        # Apply CSS for styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path("src/gui/styles.css")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), 
            css_provider, 
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Subreddit Selection Frame
        frame_reddit = Gtk.Frame(label="Query Settings")
        frame_reddit.get_style_context().add_class("ui-frames")  # Add a CSS class for targeting
        input_box.append(frame_reddit)

        # Define inputs as individual variables
        self.entry_subreddit = Gtk.Entry(text='earthporn')
        self.dropdown_timeframe = Gtk.DropDown(model=Gtk.StringList.new([timeframe.value for timeframe in Timeframe]))
        self.dropdown_timeframe.set_selected(sum([i for i, x in enumerate(Timeframe) if x == Timeframe.day]))
        self.dropdown_sort = Gtk.DropDown(model=Gtk.StringList.new([sort.value for sort in Sort]), selected=4)
        self.dropdown_sort.set_selected(sum([i for i, x in enumerate(Sort) if x == Sort.top]))
        self.dropdown_sort.connect("notify::selected", self.print_selected)
        self.entry_limit = Gtk.Entry(text='25')

        # Dictionary of labels and corresponding inputs
        label_input_reddit = {
            "Subreddit:": self.entry_subreddit,
            "Timeframe:": self.dropdown_timeframe,
            "Sort:": self.dropdown_sort,
            "Limit:": self.entry_limit
        }
        grid_reddit = self._create_input_grid(label_input_reddit)
        frame_reddit.set_child(grid_reddit)
        
        # Resolution Frame
        resolution_frame = Gtk.Frame(label="Screen Resolution Filter")
        resolution_frame.get_style_context().add_class("ui-frames")
        input_box.append(resolution_frame)

        # Target Resolution Width and Height Entries
        self.width_entry = Gtk.Entry(text=str(self.get_screen_resolution()[0]))
        self.height_entry = Gtk.Entry(text=str(self.get_screen_resolution()[1]))

        label_input_resolution = {
            "width:": self.width_entry,
            "height:": self.height_entry
        }
        grid_resolution = self._create_input_grid(label_input_resolution)
        resolution_frame.set_child(grid_resolution)

        # Download Button and Status Label
        box_dl_status = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box_main.append(box_dl_status)

        # Download Button
        self.button_download = Gtk.Button(label="Download")
        self.button_download.connect("clicked", self.on_download_clicked)
        box_dl_status.append(self.button_download)

        # Status Label
        self.status_label = Gtk.Label()
        box_dl_status.append(self.status_label)

        # Set wallpaper
        box_set_wallpaper = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box_main.append(box_set_wallpaper)
        self.button_set_wallpaper = Gtk.Button(label="Set Wallpaper")
        self.button_set_wallpaper.connect("clicked", self.on_set_wallpaper_clicked)
        box_set_wallpaper.append(self.button_set_wallpaper)

    def print_selected(self, x, _):
        print(x.get_selected_item().get_string())

    def get_screen_resolution(self):
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        return geometry.width, geometry.height

    def on_download_clicked(self, widget):
        self.status_label.set_text("Downloading...")
        subreddit = self.entry_subreddit.get_text()
        sort = self.dropdown_sort.get_selected_item().get_string()
        timeframe = self.dropdown_timeframe.get_selected_item().get_string()
        limit = int(self.entry_limit.get_text())
        target_resolution = (int(self.width_entry.get_text()), int(self.height_entry.get_text()))
        image_path = get_random_reddit_image(subreddit, sort, timeframe, limit, target_resolution)
        self.add_thumbnail(image_path)
        self.thumbnail_single_selection.set_selected(self.thumbnail_single_selection.get_n_items()-1)
        self.status_label.set_text("Downloaded to " + image_path)

    def on_set_wallpaper_clicked(self, widget):
        selected_wallpaper = self.thumbnail_single_selection.get_selected_item()
        if selected_wallpaper:
            set_gnome_background(os.path.join(self.image_folder, selected_wallpaper.filename))
        else:
            print("No item selected")

    def on_delete_wallpaper_clicked(self, widget):
        selected_wallpaper = self.thumbnail_single_selection.get_selected_item()
        if selected_wallpaper:
            os.remove(os.path.join(self.image_folder, selected_wallpaper.filename))
        else:
            print("No item selected")
    def setup_thumb_factory(self, factory, list_item):
        list_item.set_child(ThumbnailRow())

    def bind_thumb_factory(self, factory, list_item):
        row = list_item.get_child()
        thumbnail = list_item.get_item()
        if thumbnail:
            row.set_thumbnail(thumbnail)
    def load_thumbnails(self):
        self.thumbnail_model.remove_all()
        for filename in os.listdir(self.image_folder):
            if filename.lower().endswith(('.jpg', '.png', '.jpeg')):
                filepath = os.path.join(self.image_folder, filename)
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(filepath)  # Load the image without scaling
                    thumbnail = Thumbnail(pixbuf, filename)
                    self.thumbnail_model.append(thumbnail)
                except Exception as e:
                    print(f"Error loading image {filename}: {e}")
    def add_thumbnail(self, filepath):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filepath)  # Load the image without scaling
        thumbnail = Thumbnail(pixbuf, os.path.basename(filepath))
        self.thumbnail_model.append(thumbnail)
        
    @staticmethod
    def _create_input_grid(label_input_reddit):
        # Attach labels and inputs to the grid
        grid = Gtk.Grid()
        grid.set_column_spacing(6)
        grid.set_row_spacing(6)
        for i, (label_text, input_widget) in enumerate(label_input_reddit.items()):
            label = Gtk.Label(label=label_text, halign=Gtk.Align.END)
            grid.attach(label, 0, i, 1, 1)
            grid.attach(input_widget, 1, i, 1, 1)
        return grid
def on_activate(app):
    win = GRedditWallpaperWindow(application=app)
    win.set_default_size(650, 850)
    win.present()

app = Gtk.Application(application_id='com.gredditwallpaper')
app.connect('activate', on_activate)
app.run(None)
