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
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_child(main_box)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)

        # ListModel for Thumbnails
        self.thumbnail_model = Gio.ListStore(item_type=Thumbnail)
        self.load_thumbnails()

        # SingleSelection for GridView
        single_selection = Gtk.SingleSelection.new(model=self.thumbnail_model)

        # ScrolledWindow for GridView
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)  # Allow scrolling if the content is too tall
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # GridView for Thumbnails
        self.grid_view = Gtk.GridView(model=single_selection)
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.setup_factory)
        factory.connect("bind", self.bind_factory)
        self.grid_view.set_factory(factory)

        scrolled_window.set_child(self.grid_view)
        main_box.append(scrolled_window)

        # Subreddit Selection Frame
        subreddit_frame = Gtk.Frame()
        subreddit_frame.set_margin_top(10)
        subreddit_frame.set_margin_bottom(10)
        subreddit_frame.set_margin_start(10)
        subreddit_frame.set_margin_end(10)
        main_box.append(subreddit_frame)

        # Subreddit Frame Grid
        grid = Gtk.Grid()
        grid.set_column_spacing(6)
        grid.set_row_spacing(6)
        subreddit_frame.set_child(grid)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_margin_start(10)
        # Add labels and inputs to the grid
        labels = ["Subreddit:", "Timeframe:", "Sort:", "Limit:"]
        inputs = [Gtk.Entry(), Gtk.DropDown(), Gtk.DropDown(), Gtk.Entry()]
        inputs[0].set_text("earthporn")  # Subreddit entry
        inputs[1].set_model(Gtk.StringList())  # Timeframe dropdown
        [inputs[1].get_model().append(timeframe.value) for timeframe in Timeframe]
        inputs[2].set_model(Gtk.StringList())  # Sort dropdown
        [inputs[2].get_model().append(sort.value) for sort in Sort]
        inputs[3].set_placeholder_text("Limit")  # Limit entry

        for i, (label_text, input_widget) in enumerate(zip(labels, inputs)):
            label = Gtk.Label(label=label_text, halign=Gtk.Align.END)
            grid.attach(label, 0, i, 1, 1)
            grid.attach(input_widget, 1, i, 1, 1)

        # Resolution Frame
        resolution_frame = Gtk.Frame()
        resolution_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        resolution_frame.set_child(resolution_box)
        resolution_box.set_margin_top(10)
        resolution_box.set_margin_bottom(10)
        resolution_box.set_margin_start(10)
        resolution_box.set_margin_end(10)
        main_box.append(resolution_frame)

        # Target Resolution Width and Height Entries
        self.width_entry = Gtk.Entry()
        self.width_entry.set_text(str(self.get_screen_resolution()[0]))
        resolution_box.append(self.width_entry)

        self.height_entry = Gtk.Entry()
        self.height_entry.set_text(str(self.get_screen_resolution()[1]))
        resolution_box.append(self.height_entry)

        # Download Button and Status Label
        download_status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_box.append(download_status_box)

        # Download Button
        self.download_button = Gtk.Button(label="Download")
        self.download_button.connect("clicked", self.on_download_clicked)
        download_status_box.append(self.download_button)

        # Status Label
        self.status_label = Gtk.Label()
        download_status_box.append(self.status_label)

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

def on_activate(app):
    win = RedWallWindow(application=app)
    win.set_default_size(650, 850)
    win.present()

app = Gtk.Application(application_id='com.redwall')
app.connect('activate', on_activate)
app.run(None)
