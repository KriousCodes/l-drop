import gi
import os
import subprocess
import threading
import time
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, GdkPixbuf, Notify

class LDropApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.kriouscodes.ldrop')

    def do_activate(self):
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
        self.apply_custom_styling()

        Notify.init("L-Drop")
        self.history_items = []

        self.win = Adw.ApplicationWindow(application=self, title="L-Drop")
        self.win.set_default_size(500, 750)
        
        # Set custom icon using system icon theme
        self.win.set_icon_name("com.kriouscodes.ldrop")

        # The ViewStack handles the "Pages"
        self.main_stack = Adw.ViewStack()

        # 1. HOME PAGE
        home_page = self.create_home_page()
        self.main_stack.add_titled(home_page, "home", "Home")

        # 2. SEND PAGE
        self.send_page = self.create_send_page()
        self.main_stack.add_titled(self.send_page, "send_view", "Send")

        # 3. RECEIVE PAGE
        self.receive_page = self.create_receive_page()
        self.main_stack.add_titled(self.receive_page, "receive_view", "Receive")

        # Layout container
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.add_css_class("main-bg") 
        
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        box.append(header)
        box.append(self.main_stack)
        
        self.win.set_content(box)
        self.win.present()

    def create_home_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        # FIXED: Manual margins instead of set_margin_all
        box.set_margin_top(40)
        box.set_margin_bottom(40)
        box.set_margin_start(40)
        box.set_margin_end(40)

        title = Gtk.Label(label="L-Drop")
        title.add_css_class("main-title")
        box.append(title)

        subtitle = Gtk.Label(label="Fast & Easy File Sharing")
        subtitle.add_css_class("subtitle-label")
        box.append(subtitle)

        # Spacer
        box.append(Gtk.Box(height_request=40))

        # --- SEND CARD ---
        send_btn = Gtk.Button()
        send_btn.add_css_class("menu-card")
        send_btn.connect("clicked", lambda x: self.go_to_page("send_view"))
        
        s_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        s_text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        s_label = Gtk.Label(label="Send")
        s_label.add_css_class("card-header-text")
        s_label.set_halign(Gtk.Align.START)
        s_sub = Gtk.Label(label="Share files with others")
        s_sub.add_css_class("card-desc-text")
        s_text_vbox.append(s_label)
        s_text_vbox.append(s_sub)
        
        s_icon_circle = Gtk.CenterBox()
        s_icon_circle.set_size_request(50, 50)
        s_icon_circle.add_css_class("icon-circle-blue")
        s_icon = Gtk.Image.new_from_icon_name("mail-send-symbolic")
        s_icon_circle.set_center_widget(s_icon)
        
        s_content.append(s_text_vbox)
        s_content.append(Gtk.Box(hexpand=True))
        s_content.append(s_icon_circle)
        send_btn.set_child(s_content)
        box.append(send_btn)

        # --- RECEIVE CARD ---
        recv_btn = Gtk.Button()
        recv_btn.add_css_class("menu-card")
        recv_btn.connect("clicked", lambda x: self.go_to_page("receive_view"))
        
        r_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        r_text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        r_label = Gtk.Label(label="Receive")
        r_label.add_css_class("card-header-text")
        r_label.set_halign(Gtk.Align.START)
        r_sub = Gtk.Label(label="Get files from others")
        r_sub.add_css_class("card-desc-text")
        r_text_vbox.append(r_label)
        r_text_vbox.append(r_sub)
        
        r_icon_circle = Gtk.CenterBox()
        r_icon_circle.set_size_request(50, 50)
        r_icon_circle.add_css_class("icon-circle-purple")
        r_icon = Gtk.Image.new_from_icon_name("folder-download-symbolic")
        r_icon_circle.set_center_widget(r_icon)
        
        r_content.append(r_text_vbox)
        r_content.append(Gtk.Box(hexpand=True))
        r_content.append(r_icon_circle)
        recv_btn.set_child(r_content)
        box.append(recv_btn)

        footer = Gtk.Label(label="No internet required • Free & Secure")
        footer.add_css_class("footer-text")
        footer.set_margin_top(40)
        box.append(footer)

        history_title = Gtk.Label(label="Recent History")
        history_title.add_css_class("history-title")
        history_title.set_halign(Gtk.Align.START)
        history_title.set_margin_top(30)
        box.append(history_title)

        self.history_list = Gtk.ListBox()
        self.history_list.add_css_class("history-list")
        self.history_list.set_selection_mode(Gtk.SelectionMode.NONE)
        box.append(self.history_list)

        self.refresh_history()

        return box

    def create_send_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
        box.set_margin_top(30)
        box.set_margin_bottom(30)
        box.set_margin_start(30)
        box.set_margin_end(30)
        box.set_valign(Gtk.Align.CENTER)
        
        back = Gtk.Button(label="← Back")
        back.add_css_class("pill")
        back.connect("clicked", lambda x: self.go_to_page("home"))
        box.append(back)

        self.send_status = Gtk.Label(label="Ready to Send")
        box.append(self.send_status)

        self.code_display = Gtk.Label(label="---")
        self.code_display.add_css_class("code-text")
        self.code_display.set_selectable(True)
        box.append(self.code_display)

        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        preview_box.add_css_class("preview-box")
        preview_box.set_valign(Gtk.Align.CENTER)
        self.preview_image = Gtk.Image()
        self.preview_image.add_css_class("preview-image")
        self.preview_label = Gtk.Label(label="No file selected")
        self.preview_label.add_css_class("preview-label")
        preview_box.append(self.preview_image)
        preview_box.append(self.preview_label)
        box.append(preview_box)

        drop_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        drop_area.add_css_class("drop-area")
        drop_area.set_size_request(-1, 140)
        drop_area.set_valign(Gtk.Align.CENTER)
        drop_label = Gtk.Label(label="Drag & drop a file here")
        drop_label.add_css_class("drop-label")
        drop_area.append(drop_label)
        box.append(drop_area)

        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_send_drop)
        drop_area.add_controller(drop_target)

        self.select_btn = Gtk.Button(label="Select File")
        self.select_btn.add_css_class("action-btn")
        self.select_btn.connect("clicked", self.on_send_clicked)
        box.append(self.select_btn)

        self.send_another_btn = Gtk.Button(label="Send Another File")
        self.send_another_btn.add_css_class("action-btn")
        self.send_another_btn.connect("clicked", self.on_send_another_clicked)
        self.send_another_btn.set_visible(False)
        box.append(self.send_another_btn)
        return box

    def create_receive_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
        box.set_margin_top(30)
        box.set_margin_bottom(30)
        box.set_margin_start(30)
        box.set_margin_end(30)
        box.set_valign(Gtk.Align.CENTER)

        back = Gtk.Button(label="← Back")
        back.add_css_class("pill")
        back.connect("clicked", lambda x: self.go_to_page("home"))
        box.append(back)

        self.recv_status = Gtk.Label(label="Enter code")
        box.append(self.recv_status)

        self.code_entry = Gtk.Entry()
        self.code_entry.set_placeholder_text("0-word-word")
        self.code_entry.add_css_class("styled-entry")
        box.append(self.code_entry)

        btn = Gtk.Button(label="Download")
        btn.add_css_class("action-btn")
        btn.connect("clicked", self.on_recv_clicked)
        box.append(btn)
        return box

    def go_to_page(self, name):
        self.main_stack.set_visible_child_name(name)

    def apply_custom_styling(self):
        css = b"""
        .main-bg { background: linear-gradient(180deg, #6200ea 0%, #aa00ff 100%); }
        .main-title { font-size: 42pt; font-weight: 800; color: white; }
        .subtitle-label { color: rgba(255,255,255,0.8); font-size: 12pt; }
        .menu-card {
            background-color: white;
            border-radius: 24px;
            padding: 25px;
            margin-bottom: 10px;
        }
        .card-header-text { color: #333; font-size: 20pt; font-weight: bold; }
        .card-desc-text { color: #777; font-size: 11pt; }
        .icon-circle-blue { background-color: #6200ea; border-radius: 50px; color: white; }
        .icon-circle-purple { background-color: #d500f9; border-radius: 50px; color: white; }
        .footer-text { color: rgba(255,255,255,0.7); font-size: 10pt; }
        .code-text { font-family: 'Monospace'; font-size: 32pt; color: white; font-weight: bold; }
        .action-btn { background-color: white; color: #6200ea; border-radius: 50px; padding: 15px; font-weight: bold; font-size: 14pt; }
        .pill { background: rgba(255,255,255,0.2); color: white; border-radius: 50px; border: none; }
        .styled-entry { border-radius: 12px; padding: 10px; background: white; color: black; }
        .preview-box { padding: 10px; }
        .preview-label { color: rgba(255,255,255,0.85); font-size: 10pt; }
        .preview-image { min-width: 96px; min-height: 96px; }
        .history-title { color: rgba(255,255,255,0.9); font-size: 12pt; font-weight: bold; }
        .history-list { background: transparent; }
        .history-row { color: rgba(255,255,255,0.85); font-size: 10pt; }
        .drop-area {
            border-radius: 16px;
            border: 2px dashed rgba(255,255,255,0.6);
            padding: 18px;
        }
        .drop-label { color: rgba(255,255,255,0.85); font-size: 12pt; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def on_send_clicked(self, button):
        dialog = Gtk.FileDialog()
        dialog.open(self.win, None, self.on_file_selected)

    def on_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            path = file.get_path()
            if not path:
                return
            self.handle_selected_file(path)
        except: pass

    def on_send_drop(self, drop_target, value, x, y):
        files = value.get_files() if value else []
        if not files:
            return False
        path = files[0].get_path()
        if not path:
            return False
        self.handle_selected_file(path)
        return True

    def handle_selected_file(self, path):
        self.reset_send_ui()
        self.send_status.set_text("Preparing...")
        self.update_preview(path)
        threading.Thread(target=self.run_send, args=(path,), daemon=True).start()

    def update_preview(self, path):
        file = Gio.File.new_for_path(path)
        info = file.query_info(
            "standard::content-type,standard::icon,thumbnail::path",
            Gio.FileQueryInfoFlags.NONE,
            None,
        )

        content_type = info.get_content_type() or ""
        filename = os.path.basename(path)
        self.preview_label.set_text(filename)

        thumbnail_path = info.get_attribute_byte_string("thumbnail::path")
        if thumbnail_path:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(thumbnail_path, 128, 128, True)
                self.preview_image.set_from_pixbuf(pixbuf)
                return
            except Exception:
                pass

        if content_type.startswith("image/"):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 128, 128, True)
                self.preview_image.set_from_pixbuf(pixbuf)
                return
            except Exception:
                pass

        icon = info.get_icon()
        if icon:
            self.preview_image.set_from_gicon(icon)
        else:
            self.preview_image.clear()

    def run_send(self, path):
        proc = subprocess.Popen(["wormhole", "send", path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            if "Wormhole code is:" in line:
                GLib.idle_add(self.code_display.set_text, line.split("is:")[1].strip())
                GLib.idle_add(self.send_status.set_text, "Code ready")
            if "Transfer complete" in line:
                GLib.idle_add(self.send_status.set_text, "✓ Sent!")
                GLib.idle_add(self.add_history_item, "Sent", path)
                GLib.idle_add(self.notify, "File Sent", os.path.basename(path))
                GLib.idle_add(self.show_send_another)
                break

    def on_recv_clicked(self, button):
        code = self.code_entry.get_text().strip()
        if not code: return
        download_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
        if not download_dir:
            download_dir = os.path.expanduser("~")
        path = os.path.join(download_dir, "L-Drop Saves")
        if not os.path.exists(path): os.makedirs(path)
        threading.Thread(target=self.run_receive, args=(code, path), daemon=True).start()

    def run_receive(self, code, path):
        proc = subprocess.Popen(["wormhole", "receive", "--accept-file", code], cwd=path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            if "%" in line:
                p = [x for x in line.split() if "%" in x][0]
                GLib.idle_add(self.recv_status.set_text, f"Downloading: {p}")
        proc.wait()
        GLib.idle_add(self.recv_status.set_text, "✓ Done!")
        GLib.idle_add(self.add_history_item, "Received", path)
        GLib.idle_add(self.notify, "File Received", f"Ready in {path}")
        subprocess.Popen(["xdg-open", path])

    def notify(self, title, message):
        try:
            notification = Notify.Notification.new(title, message)
            notification.show()
        except Exception:
            pass

    def on_send_another_clicked(self, button):
        self.reset_send_ui()

    def reset_send_ui(self):
        self.send_status.set_text("Ready to Send")
        self.code_display.set_text("---")
        self.select_btn.set_visible(True)
        self.send_another_btn.set_visible(False)

    def show_send_another(self):
        self.select_btn.set_visible(False)
        self.send_another_btn.set_visible(True)

    def add_history_item(self, kind, path):
        name = os.path.basename(path.rstrip("/"))
        label = f"{kind}: {name}"
        self.history_items.insert(0, label)
        self.history_items = self.history_items[:5]
        self.refresh_history()

    def refresh_history(self):
        if not hasattr(self, "history_list"):
            return
        child = self.history_list.get_first_child()
        while child:
            self.history_list.remove(child)
            child = self.history_list.get_first_child()

        if not self.history_items:
            row = Gtk.Label(label="No recent activity")
            row.add_css_class("history-row")
            row.set_halign(Gtk.Align.START)
            self.history_list.append(row)
            return

        for item in self.history_items:
            row = Gtk.Label(label=item)
            row.add_css_class("history-row")
            row.set_halign(Gtk.Align.START)
            self.history_list.append(row)

app = LDropApp()
app.run(None)
