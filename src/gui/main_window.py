import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, GObject, Gio
import os
from src.redwall import Timeframe, Sort

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

class RedWallWindow(Gtk.ApplicationWindow):
    def __init__(self, **kargs):
        super().__init__(**kargs, title='RedWall')
        box_main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box_main.set_name("box_main")
        self.set_child(box_main)

        # ListModel for Thumbnails
        self.thumbnail_model = Gio.ListStore(item_type=Thumbnail)
        self.load_thumbnails()

        # ScrolledWindow for GridView
        scrolled_window = Gtk.ScrolledWindow(vexpand=True)
        
        # GridView for Thumbnails
        self.grid_view = Gtk.GridView(model=Gtk.SingleSelection.new(model=self.thumbnail_model))
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.setup_factory)
        factory.connect("bind", self.bind_factory)
        self.grid_view.set_factory(factory)

        scrolled_window.set_child(self.grid_view)
        box_main.append(scrolled_window)

        input_box = Gtk.Box(spacing=10)
        box_main.append(input_box)
        # Apply CSS for styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path("styles.css")
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
        entry_subreddit = Gtk.Entry(text='earthporn')
        dropdown_timeframe = Gtk.DropDown(model=Gtk.StringList.new([timeframe.value for timeframe in Timeframe]))
        dropdown_timeframe.set_selected(sum([i for i, x in enumerate(Timeframe) if x == Timeframe.day]))
        dropdown_sort = Gtk.DropDown(model=Gtk.StringList.new([sort.value for sort in Sort]), selected=4)
        dropdown_sort.set_selected(sum([i for i, x in enumerate(Sort) if x == Sort.top]))
        dropdown_sort.connect("notify::selected", self.print_selected)
        entry_limit = Gtk.Entry(text='25')

        # Dictionary of labels and corresponding inputs
        label_input_reddit = {
            "Subreddit:": entry_subreddit,
            "Timeframe:": dropdown_timeframe,
            "Sort:": dropdown_sort,
            "Limit:": entry_limit
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
        self.download_button = Gtk.Button(label="Download")
        self.download_button.connect("clicked", self.on_download_clicked)
        box_dl_status.append(self.download_button)

        # Status Label
        self.status_label = Gtk.Label()
        box_dl_status.append(self.status_label)
    def print_selected(self, x, _):
        print(x.get_selected_item().get_string())
    def get_screen_resolution(self):
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        return geometry.width, geometry.height

    def on_download_clicked(self, widget):
        self.status_label.set_text("Downloading...")
        self.load_thumbnails()
    def setup_factory(self, factory, list_item):
        list_item.set_child(ThumbnailRow())

    def bind_factory(self, factory, list_item):
        row = list_item.get_child()
        thumbnail = list_item.get_item()
        if thumbnail:
            row.set_thumbnail(thumbnail)
    def load_thumbnails(self):
        image_folder = os.path.join(os.getcwd(), "images")
        self.thumbnail_model.remove_all()
        for filename in os.listdir(image_folder):
            if filename.lower().endswith(('.jpg', '.png', '.jpeg')):
                filepath = os.path.join(image_folder, filename)
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(filepath)  # Load the image without scaling
                    thumbnail = Thumbnail(pixbuf, filename)
                    self.thumbnail_model.append(thumbnail)
                except Exception as e:
                    print(f"Error loading image {filename}: {e}")
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
    win = RedWallWindow(application=app)
    win.set_default_size(650, 850)
    win.present()

app = Gtk.Application(application_id='com.redwall')
app.connect('activate', on_activate)
app.run(None)
