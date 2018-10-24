# from multiprocessing import Process
import sys
import subprocess
import scanner
import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, Gtk, Gdk

class GstWidget(Gtk.Box):
    def __init__(self, pipeline):
        super().__init__()
        # Only setup the widget after the window is shown.
        self.connect('realize', self._on_realize)

        # Parse a gstreamer pipeline and create it.
        self._bin = Gst.parse_bin_from_description(pipeline, True)

    def _on_realize(self, widget):
        global pipeline
        pipeline = Gst.Pipeline()
        factory = pipeline.get_factory()
        gtksink = factory.make('gtksink')
        pipeline.add(self._bin)
        pipeline.add(gtksink)
        # Link the pipeline to the sink that will display the video (in our case it is Gtk).
        self._bin.link(gtksink)
        self.pack_start(gtksink.props.widget, True, True, 0)
        gtksink.props.widget.show()
        # Start the video
        pipeline.set_state(Gst.State.PLAYING)

class ScanDialog(Gtk.Dialog): # Dialog to select from list of Pi's

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Select your Pi", parent, 0)

        self.set_default_size(150, 100)

        button1 = Gtk.RadioButton.new_with_label_from_widget(None, pii_ip[0])
        button1.connect("toggled", self.on_button_toggled, "1")

        button2 = Gtk.RadioButton.new_from_widget(button1)
        button2.set_label(pii_ip[1])
        button2.connect("toggled", self.on_button_toggled, "2")

        box = self.get_content_area()
        box.add(button1)
        box.add(button2)

        def on_button_toggled(self, button, name):
            if button.get_active():
                return button.get_label()

        self.show_all()

class ButtonWindow(Gtk.Window): #The controls window

    def __init__(self):
        Gtk.Window.__init__(self, title="Controls")
        self.set_border_width(10)

        hbox = Gtk.Box(spacing=6)
        self.add(hbox)

        button = Gtk.ToggleButton("Play/Pause", use_underline=True)
        button.connect("toggled", self.on_button_toggled, "2")
        hbox.pack_start(button, True, True, 0)

        button = Gtk.Button.new_with_mnemonic("_Capture")
        button.connect("clicked", self.on_capture_clicked)
        hbox.pack_start(button, True, True, 0)

        button = Gtk.Button.new_with_mnemonic("_Record")
        button.connect("clicked", self.on_record_clicked)
        hbox.pack_start(button, True, True, 0)

    def on_button_toggled(self, button, name):
        if button.get_active():
            pipeline.set_state(Gst.State.PAUSED)
        else:
            pipeline.set_state(Gst.State.PLAYING)

    def on_capture_clicked(self, button):
        screen_capture(main_window, button_window)

    def on_record_clicked(self, button):
        screen_record(main_window, button_window)

class StartWindow(Gtk.Window): # Start screen

    def __init__(self):
        Gtk.Window.__init__(self, title="Raspicam Streamer")
        self.set_border_width(10)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        hbox = Gtk.Box(spacing=6)
        vbox.pack_start(hbox, True, True, 0)

        self.popover = Gtk.Popover()
        pbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        pbox.pack_start(Gtk.ModelButton("Item 1"), False, True, 10)
        pbox.pack_start(Gtk.Label("Item 2"), False, True, 10)
        self.popover.add(pbox)
        self.popover.set_position(Gtk.PositionType.RIGHT)

        self.scanning = Gtk.ProgressBar()
        vbox.pack_start(self.scanning, True, True, 0)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("or enter your Pi's IP Address here.")
        vbox.pack_start(self.entry, True, True, 0)

        button1 = Gtk.Button.new_with_mnemonic("_Scan for Cameras")
        button1.connect("clicked", self.on_scan_clicked)
        self.close()
        hbox.pack_start(button1, True, True, 0)

        button2 = Gtk.Button.new_with_mnemonic("_Connect")
        button2.connect("clicked", self.on_connect_clicked)
        vbox.pack_start(button2, True, True, 0)

    def on_scan_clicked(self, button):
        self.scanning.pulse()
        pii_ip = scanner.scan() #call scanner here
        global pi_ip
        if len(pii_ip) != 0:
            if len(pii_ip) > 1:
                self.popover.set_relative_to(button)
                self.popover.show_all()
                self.popover.popup()
            else:
                pi_ip = pii_ip[0][1]
            self.close()
            gst_live()
        else:
            print("Not found")

    def on_connect_clicked(self, button):
        global pi_ip
        pi_ip = self.entry.get_text()
        self.close()
        gst_live()

class MainWindow(Gtk.Window): #Video window

    def __init__(self):
        Gtk.Window.__init__(self, title="Raspicam Streamer - Video")

#        self.connect("key-press-event", self.on_key_press_event)

'''    def on_key_press_event(self, widget, event):
        global playing
        if event.keyval == Gdk.KEY_c:
            screen_capture(self)
            print("Frame captured.")
        elif event.keyval == Gdk.KEY_r:
            screen_record(self)
        elif event.keyval == Gdk.KEY_p:
            if playing == True:
                pipeline.set_state(Gst.State.PAUSED)
                playing = False
            else:
                pipeline.set_state(Gst.State.PLAYING)
                playing = True
'''
class PlayerGroup(Gtk.WindowGroup):
    def __init__(self):
        Gtk.WindowGroup.__init__(self)

def screen_capture(win1, win2): #capture method
    win1.close()
    win2.close()
    ffmpeg_cap()
    gst_live()

def screen_record(win1, win2): # record method
    win1.close()
    win2.close()
    t = 10
    if t<7:
        t=7
    ffmpeg_rec(t+1)
    gst_live()

def gst_live():
    gst_cmd = 'souphttpsrc location=http://'+ pi_ip +':8080/stream/video.h264 ! h264parse ! avdec_h264 ! videoconvert'

    Gst.init(None)
    Gst.init_check(None)
    global main_window, button_window
    main_window = MainWindow()
    button_window = ButtonWindow()
    # Create a gstreamer pipeline with no sink.
    # A sink will be created inside the GstWidget.
    widget = GstWidget(gst_cmd)
    widget.set_size_request(1080, 720)
    main_window.add(widget)

    player = PlayerGroup()
    player.add_window(main_window)
    player.add_window(button_window)

    main_window.show_all()
    button_window.show_all()

    print(player.get_current_grab())

    main_window.connect('destroy', Gtk.main_quit)
    button_window.connect('destroy', Gtk.main_quit)
    Gtk.main()

def start_app():
    start_window = StartWindow()
    start_window.props.default_height = 100
    start_window.props.default_width = 300
    start_window.show_all()
    start_window.connect('destroy', Gtk.main_quit)

def ffmpeg_rec(duration): #call ffmpeg to capture
    subprocess.call("ffmpeg.exe -y -r 25 -f h264 -i http://"+ pi_ip +":8080/stream/video.h264 -vcodec copy -t "+ str(duration) + " C:\\Users\Rohan\Desktop\whatever.mp4", shell=True)

def ffmpeg_cap(): # call ffmpeg to record
    subprocess.call("ffmpeg.exe -y -r 25 -f h264 -i http://"+ pi_ip +":8080/stream/video.h264 -r 1 -f image2 -t 1 C:\\Users\Rohan\Desktop\capture-%2d.jpg", shell=True)

if __name__ == "__main__":
    playing = True
    start_app()
    Gtk.main()
