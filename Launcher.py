#!/usr/bin/env python3
import json
import os
import sys
import subprocess
import platform
import subprocess
import platform
import logging

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, Scrollbar
    _REAL_TK = True
except ModuleNotFoundError:
    _REAL_TK = False 

    class _BaseWidget:
        def __init__(self, *a, **kw): pass
        def pack(self, *a, **kw): pass
        def grid(self, *a, **kw): pass
        def place(self, *a, **kw): pass
        def bind(self, *a, **kw): pass
        def configure(self, *a, **kw): pass
        def destroy(self): pass
        def pack_propagate(self, *a, **kw): pass
        def bind_all(self, *a, **kw): pass

    class _DummyTk(_BaseWidget):
        def title(self, *a, **kw): pass
        def geometry(self, *a, **kw): pass
        def resizable(self, *a, **kw): pass
        def mainloop(self, *a, **kw): pass
        def configure(self, *a, **kw): pass

    class _DummyIntVar:
        def __init__(self, *a, **kw): self._v = 0
        def get(self): return self._v
        def set(self, v): self._v = v

    class _DummyCanvas(_BaseWidget):
        def __init__(self, *a, **kw):
            self._y = 0
            self._region = (0, 0, 0, 0)
            # store items so itemconfig can be called
            self._items = {}

        def yview(self, *a, **kw):
            return (self._y, self._y + 0.1)

        def yview_scroll(self, delta, what):
            self._y = max(0.0, min(1.0, self._y + delta * 0.01))

        def configure(self, **kw):
        # capture the yscrollcommand that the scrollbar will call
            self.yscrollcommand = kw.get('yscrollcommand', None)

        def bbox(self, tag):
            return self._region

        def create_window(self, *a, **kw): pass
        def create_oval(self, *a, **kw):
        # return a fake item id and store its options
            item_id = len(self._items) + 1
            self._items[item_id] = {}
            return item_id
        def create_rectangle(self, *a, **kw): pass
        def create_text(self, *a, **kw): pass

        def itemconfig(self, item, **options):
            if item not in self._items:
                self._items[item] = {}
            self._items[item].update(options)

        def itemcget(self, item, option):
            return self._items.get(item, {}).get(option, None)

    class _DummyStyle:
        def __init__(self, *a, **kw): pass
        def theme_use(self, *a, **kw): pass
        def configure(self, *a, **kw): pass
        def map(self, *a, **kw): pass

    # ---------- ttk.Scrollbar stub ----------
    class _DummyScrollbar(_BaseWidget):
        def __init__(self, master=None, **kw):
            self.command = kw.get('command', None)

        def set(self, *a, **kw):
            pass

    tk = type('tk', (), {
        'X':      'x',
        'Y':      'y',
        'BOTH':   'both',
        'LEFT':   'left',
        'RIGHT':  'right',
        'TOP':    'top',
        'BOTTOM': 'bottom',
        'CENTER': 'center',
        'W':      'w',
        'Tk':      _DummyTk,
        'Frame':   _BaseWidget,
        'Canvas':  _DummyCanvas,
        'Label':   _BaseWidget,
        'Button':  _BaseWidget,
        'IntVar':  _DummyIntVar,
    })

    ttk = type('ttk', (), {
        'Style':      _DummyStyle,
        'Frame':      _BaseWidget,
        'Label':      _BaseWidget,
        'Button':     _BaseWidget,
        'Scrollbar':  _DummyScrollbar,
    })

    messagebox = type('messagebox', (), {
        'showerror':   lambda *a, **kw: print("ERROR:",   a[1] if len(a) > 1 else ""),
        'showwarning': lambda *a, **kw: print("WARNING:", a[1] if len(a) > 1 else ""),
        'showinfo':    lambda *a, **kw: print("INFO:",    a[1] if len(a) > 1 else ""),
    })

class GameLauncher:
    def __init__(self, root):
        logging.debug("Initializing GameLauncher...")
        self.root = root
        self.root.title("Game Launcher")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        self.colors = {
            "background": "#282c34",
            "header_bg": "#23272e",
            "panel_bg": "#323740",
            "panel_border": "#464e5a",
            "text": "#c8c8c8",
            "highlight": "#0084ff",
            "button_bg": "#3c424d",
            "button_hover": "#505866",
            "button_text": "#dcdcdc",
            "radio_bg": "#464e5a",
            "radio_selected": "#0084ff",
            "radio_border": "#646e7d",
            "path_text": "#969696"
        }
        
        self.configure_styles()
        self.load_config()
        self.create_widgets()

    def configure_styles(self):
        logging.debug("Configuring styles...")
        style = ttk.Style()
        style.theme_use('clam')
        self.root.configure(bg=self.colors["background"])
        style.configure('.', background=self.colors["background"], foreground=self.colors["text"])
        
        style.configure('Panel.TFrame', background=self.colors["panel_bg"])
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'), background=self.colors["header_bg"], foreground=self.colors["text"])
        style.configure('SubHeader.TLabel', font=('Arial', 12, 'bold'), background=self.colors["panel_bg"], foreground=self.colors["text"])
        style.configure('TButton', background=self.colors["button_bg"], foreground=self.colors["button_text"], borderwidth=0, font=('Arial', 10, 'bold'), padding=5)
        
        style.map('TButton', background=[('active', self.colors["button_hover"]), ('pressed', self.colors["radio_bg"])])

    def load_config(self):
        try:
            logging.debug("Loading configuration...")
            if getattr(sys, 'frozen', False):
                self.base_dir = os.path.dirname(os.path.abspath(sys.executable))
            else:
                self.base_dir = os.path.dirname(os.path.abspath(__file__))

            config_path = os.path.join(self.base_dir, 'config.json')

            if not os.path.exists(config_path):
                self.create_default_config()
                
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.game_name = config.get("game_name", "Unknown Game")
                self.options = self.parse_options(config.get("options", []))
                self.umu_commands = config.get("umu_commands", {})
                
            logging.debug(f"Loaded configuration from {config_path}")
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            messagebox.showerror("Error", f"Failed to load config: {str(e)}")
            self.options = []
            self.game_name = "Game Launcher"
            self.create_default_config()

    def create_default_config(self):
        logging.debug("Creating default configuration...")

        if getattr(sys, 'frozen', False):
            config_path = os.path.join(sys._MEIPASS, 'config.json')
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, 'config.json')

        default_config = {
            "game_name": "Game",
            "options": [
                {
                    "name": "Play Game",
                    "path": "game/mygame.exe",
                    "launch_options": ["-EpicPortal"],
                    "use_wine": 0
                },
                {
                    "name": "Play Windows Game",
                    "path": "mygame.exe",
                    "launch_options": ["-EpicPortal"],
                    "use_wine": 0
                },
                {
                    "name": "Play Linux Game",
                    "path": "mygame.x86_64",
                    "launch_options": [""]
                },
                {
                    "name": "Play macOS Game",
                    "path": "mygame.app",
                    "launch_options": []
                }
            ],
            "umu_commands": {
                "GAMEID": "1234",
                "PROTONPATH": "GE-Proton10-28",
                "pre_launch": ["GAMEID=1234", "PROTONPATH=GE-Proton10-28"]
            }
        }
    
        if not os.path.exists("config.json"):
            with open("config.json", "w") as f:
                json.dump(default_config, f, indent=4)

        logging.debug(f"Created default configuration at {config_path}")

    def parse_options(self, options_list):
        parsed = []
        for option in options_list:
            if isinstance(option, dict) and "name" in option and "path" in option:
                parsed.append({
                    "name": option["name"],
                    "path": option["path"],
                    "launch_options": option.get("launch_options", []),
                    "use_wine": option.get("use_wine", 0)
                })
        return parsed

    def create_widgets(self):
        logging.debug("Creating widgets...")
        header_frame = ttk.Frame(self.root, style='Panel.TFrame', height=50)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(header_frame, text=self.game_name, style='Header.TLabel', anchor=tk.CENTER).pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        option_frame = ttk.Frame(self.root, style='Panel.TFrame', height=40)
        option_frame.pack(fill=tk.X, pady=(0, 10))
        
        option_count = len(self.options)
        ttk.Label(option_frame, text=f"Select Launch Option ({option_count})", style='SubHeader.TLabel', anchor=tk.CENTER).pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        content_frame = tk.Frame(self.root, bg=self.colors["panel_border"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        inner_frame = tk.Frame(content_frame, bg=self.colors["panel_bg"])
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        self.canvas = tk.Canvas(inner_frame, bg=self.colors["panel_bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(inner_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors["panel_bg"])
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.selected_option = tk.IntVar(value=0)
        for idx, option in enumerate(self.options):
            self.create_custom_radio(idx, option)
        
        button_frame = tk.Frame(self.root, bg=self.colors["background"])
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        cancel_btn = tk.Button(button_frame, text="Cancel", bg=self.colors["button_bg"], fg=self.colors["button_text"], activebackground=self.colors["button_hover"], activeforeground=self.colors["button_text"], bd=0, font=('Arial', 10, 'bold'), padx=15, pady=5, command=self.root.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        start_btn = tk.Button(button_frame, text="Start", bg=self.colors["button_bg"], fg=self.colors["button_text"], activebackground=self.colors["button_hover"], activeforeground=self.colors["button_text"], bd=0, font=('Arial', 10, 'bold'), padx=15, pady=5, command=self.launch_game)
        start_btn.pack(side=tk.LEFT, padx=10)
        
        button_frame.pack_propagate(False)
        button_frame.configure(height=50)
        
        button_container = tk.Frame(button_frame, bg=self.colors["background"])
        button_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        start_btn.pack(side=tk.RIGHT, padx=5)

    def create_custom_radio(self, idx, option):
        frame = tk.Frame(self.scrollable_frame, bg=self.colors["panel_bg"], padx=10, pady=5)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        radio_canvas = tk.Canvas(frame, width=20, height=20, bg=self.colors["panel_bg"], highlightthickness=0)
        radio_canvas.pack(side=tk.LEFT, padx=(5, 10))
        
        radio_canvas.create_oval(2, 2, 18, 18, outline=self.colors["radio_border"], width=1, fill=self.colors["panel_bg"])
        
        inner_circle = radio_canvas.create_oval(6, 6, 14, 14, outline="", fill=self.colors["panel_bg"])
        
        text_frame = tk.Frame(frame, bg=self.colors["panel_bg"])
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        name_label = tk.Label(text_frame, text=option["name"], bg=self.colors["panel_bg"], fg=self.colors["text"], font=('Arial', 11), anchor=tk.W)
        name_label.pack(fill=tk.X, padx=(0, 5))
        
        path_label = tk.Label(text_frame, text=option["path"], bg=self.colors["panel_bg"], fg=self.colors["path_text"], font=('Arial', 9), anchor=tk.W)
        path_label.pack(fill=tk.X, padx=(0, 5))
        
        def select_option():
            self.selected_option.set(idx)
            for child in self.scrollable_frame.winfo_children():
                if hasattr(child, 'inner_circle'):
                    color = self.colors["radio_selected"] if child.idx == idx else self.colors["panel_bg"]
                    child.canvas.itemconfig(child.inner_circle, fill=color)
    
        frame.idx = idx
        frame.canvas = radio_canvas
        frame.inner_circle = inner_circle
    
        if idx == 0:
            radio_canvas.itemconfig(inner_circle, fill=self.colors["radio_selected"])
    
        frame.bind("<Button-1>", lambda e: select_option())
        radio_canvas.bind("<Button-1>", lambda e: select_option())
        name_label.bind("<Button-1>", lambda e: select_option())
        path_label.bind("<Button-1>", lambda e: select_option())

    def launch_game(self):
        logging.debug("Start button clicked, attempting to launch the game...")

        if not self.options:
            logging.warning("No options available")
            messagebox.showwarning("No Options", "No launch options available")
            return

        idx = self.selected_option.get()
        if idx < 0 or idx >= len(self.options):
            logging.warning("Invalid option selected")
            messagebox.showwarning("Warning", "Please select a launch option!")
            return

        option = self.options[idx]
        path = option["path"]
        use_wine = option.get("use_wine", 0)

        abs_path = os.path.join(self.base_dir, path)

        if not os.path.isfile(abs_path):
            messagebox.showerror("File missing", f"Cannot find {abs_path}")
            return

        logging.debug(f"Attempting to launch: {abs_path}")

        system = platform.system()
        proc = None

        try:
            if system == "Windows":
                if not option.get("launch_options"):
                    os.startfile(abs_path)
                else:
                    cmd = [abs_path] + option["launch_options"]
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
                    proc = subprocess.Popen(cmd, cwd=os.path.dirname(abs_path), startupinfo=startupinfo)

            elif system == "Linux" and (path.lower().endswith(".exe") or path.lower().endswith(".bat")):
                if use_wine == 1:
                    logging.debug(f"Running with Wine: wine \"{abs_path}\"")
                    cmd = ["wine", abs_path]
                    if option.get("launch_options"):
                        cmd += option["launch_options"]
                    proc = subprocess.Popen(cmd, cwd=os.path.dirname(abs_path))
                else:
                    env = os.environ.copy()
                    if "pre_launch" in self.umu_commands:
                        for assignment in self.umu_commands["pre_launch"]:
                            if '=' in assignment:
                                key, value = assignment.split('=', 1)
                                env[key] = value
                    if "GAMEID" in self.umu_commands:
                        env["GAMEID"] = self.umu_commands["GAMEID"]
                    if "PROTONPATH" in self.umu_commands:
                        env["PROTONPATH"] = self.umu_commands["PROTONPATH"]

                    cmd = ["umu-run", abs_path]
                    if option.get("launch_options"):
                        cmd += option["launch_options"]
                
                    logging.debug(f"Running command with umu-run: {cmd}")
                    proc = subprocess.Popen(cmd, env=env, cwd=os.path.dirname(abs_path))

            elif system == "Linux":
                cmd = [abs_path]
                if option.get("launch_options"):
                    cmd += option["launch_options"]
                proc = subprocess.Popen(cmd, cwd=os.path.dirname(abs_path))

            elif system == "Darwin":
                cmd = ["open", abs_path]
                if option.get("launch_options"):
                   cmd += ["--args"] + option["launch_options"]
                proc = subprocess.Popen(cmd, cwd=os.path.dirname(abs_path))

            else:
                messagebox.showerror("Unsupported Platform", f"The current platform ({system}) is not supported.")
                return

        except Exception as e:
            logging.error(f"Launch error: {e}")
            messagebox.showerror("Launch Error", f"Failed to launch:\n{e}")

        finally:
            if _REAL_TK:
                self.root.quit()
                self.root.destroy()
            else:
                if proc is not None:
                    proc.wait()

            sys.exit(0)

if __name__ == "__main__":
    logging.debug("Starting GameLauncher...")
    root = tk.Tk()
    launcher = GameLauncher(root)
    
    try:
        root.mainloop()
    except Exception as e:
        logging.error(f"Error during Tkinter mainloop: {e}")
