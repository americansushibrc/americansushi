"""
===================================================================
AMERICAN SUSHI - GESTOR DE PRECIOS & SINCRONIZADOR CON GITHUB
Aplicación autónoma 100% en Python (Sin dependencias externas)
===================================================================
"""

import os
import sys

# Asegurar que el directorio de trabajo sea siempre la carpeta donde está este script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

import re
import json
import time
import base64
import webbrowser
import urllib.request
import urllib.error
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

CONFIG_FILE = os.path.join(BASE_DIR, "admin_config.json")
INDEX_FILE = os.path.join(BASE_DIR, "index.html")

# Paleta de colores Dark & Orange American Sushi
BG_DARK = "#12161E"        # Fondo principal
BG_CARD = "#1A222D"        # Tarjetas / Secciones
BG_INPUT = "#0E131A"       # Fondo inputs
BORDER_COLOR = "#2B374A"   # Bordes sutiles
ACCENT_ORANGE = "#F04D0B"  # Naranja identidad
ACCENT_PEACH = "#F7A072"   # Salmón
TEXT_WHITE = "#FFFFFF"     # Texto principal
TEXT_MUTED = "#8E9AA8"     # Texto secundario
SUCCESS_GREEN = "#25D366"  # Verde confirmación

class SushiAdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍣 American Sushi - Gestor de Precios")
        self.root.geometry("820x890")
        self.root.minsize(780, 720)
        self.root.configure(bg=BG_DARK)

        # Variables de precios
        self.price_vars = {}
        
        # Variables de configuración
        self.github_token_var = tk.StringVar()
        self.github_repo_var = tk.StringVar(value="americansushibrc/americansushi")
        self.github_branch_var = tk.StringVar(value="main")
        self.commit_msg_var = tk.StringVar()
        self.index_path_var = tk.StringVar(value=INDEX_FILE)
        
        # Cargar configuración previa
        self.load_admin_config()
        
        # Estilos y Construcción de UI
        self.setup_styles()
        self.build_ui()
        
        # Cargar precios automáticamente al iniciar
        self.load_prices_from_html()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=BG_DARK, foreground=TEXT_WHITE, font=("Segoe UI", 10))
        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure(
            "TNotebook.Tab", 
            background=BG_CARD, 
            foreground=TEXT_WHITE, 
            padding=[18, 9], 
            font=("Segoe UI", 10, "bold")
        )
        style.map(
            "TNotebook.Tab", 
            background=[("selected", ACCENT_ORANGE)], 
            foreground=[("selected", "#FFFFFF")]
        )

    def build_ui(self):
        # 1. ENCABEZADO
        header_frame = tk.Frame(self.root, bg=BG_CARD)
        header_frame.pack(fill="x", side="top")
        
        header_content = tk.Frame(header_frame, bg=BG_CARD)
        header_content.pack(fill="x", padx=20, pady=12)

        title_box = tk.Frame(header_content, bg=BG_CARD)
        title_box.pack(side="left")

        title_lbl = tk.Label(
            title_box, 
            text="🍣 AMERICAN SUSHI • BARILOCHE", 
            font=("Segoe UI", 15, "bold"), 
            bg=BG_CARD, 
            fg=ACCENT_PEACH
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            title_box, 
            text="Gestor Central de Precios • 100% Autónomo en Python", 
            font=("Segoe UI", 9), 
            bg=BG_CARD, 
            fg=TEXT_MUTED
        )
        subtitle_lbl.pack(anchor="w")

        # Botones superiores de acceso rápido
        btn_box = tk.Frame(header_content, bg=BG_CARD)
        btn_box.pack(side="right")

        preview_btn = tk.Button(
            btn_box,
            text="🌐 Ver Sitio en Navegador",
            command=self.open_local_preview,
            bg="#242E3D",
            fg=TEXT_WHITE,
            activebackground="#344358",
            activeforeground=TEXT_WHITE,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2"
        )
        preview_btn.pack(side="left", padx=(0, 6))

        reload_btn = tk.Button(
            btn_box,
            text="🔄 Recargar",
            command=self.load_prices_from_html,
            bg="#242E3D",
            fg=TEXT_WHITE,
            activebackground=ACCENT_ORANGE,
            activeforeground=TEXT_WHITE,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2"
        )
        reload_btn.pack(side="left")

        # 2. PESTAÑAS
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=16, pady=10)

        tab_prices = tk.Frame(notebook, bg=BG_DARK)
        notebook.add(tab_prices, text="  🏷️ Precios de la Carta  ")

        tab_github = tk.Frame(notebook, bg=BG_DARK)
        notebook.add(tab_github, text="  🐙 Conexión con GitHub (Opcional)  ")

        self.build_prices_tab(tab_prices)
        self.build_github_tab(tab_github)

        # 3. CONSOLA DE ESTADO (LOG INTEGRADO)
        log_frame = tk.LabelFrame(
            self.root, 
            text=" 📜 Estado & Acciones en Vivo ", 
            bg=BG_DARK, 
            fg=ACCENT_PEACH,
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=6
        )
        log_frame.pack(fill="x", padx=16, pady=(0, 10))

        self.log_text = tk.Text(
            log_frame, 
            height=4, 
            bg="#0B0E14", 
            fg="#9FB3C8", 
            font=("Consolas", 9), 
            wrap="word", 
            relief="flat",
            padx=8,
            pady=6
        )
        self.log_text.pack(fill="x")
        self.log_text.config(state="disabled")

        # 4. BOTONERA DE ACCIÓN PRINCIPAL
        actions_frame = tk.Frame(self.root, bg=BG_DARK)
        actions_frame.pack(fill="x", padx=16, pady=(0, 16))

        save_local_btn = tk.Button(
            actions_frame,
            text="💾 1. Guardar en index.html",
            command=self.save_local_only,
            bg=ACCENT_ORANGE,
            fg="#FFFFFF",
            activebackground="#D94005",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            pady=11,
            cursor="hand2"
        )
        save_local_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        publish_btn = tk.Button(
            actions_frame,
            text="🚀 2. Publicar Directo a GitHub",
            command=self.save_and_publish,
            bg="#2A3547",
            fg=TEXT_WHITE,
            activebackground="#37455C",
            activeforeground=TEXT_WHITE,
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            pady=11,
            cursor="hand2"
        )
        publish_btn.pack(side="right", fill="x", expand=True, padx=(8, 0))

    def build_prices_tab(self, parent):
        canvas = tk.Canvas(parent, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG_DARK)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=770)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 1. TABLAS DE SUSHI
        self.create_section_card(
            scrollable_frame,
            title="🍣 TABLAS DE SUSHI (COMBOS)",
            fields=[
                ("12 Piezas Variadas ($)", "p_12_var", 30000),
                ("12 Piezas Premium ($)", "p_12_prem", 31000),
                ("20 Piezas Variadas ($)", "p_20_var", 42000),
                ("20 Piezas Premium ($)", "p_20_prem", 48000),
                ("30 Piezas Variadas ($)", "p_30_var", 62000),
                ("30 Piezas Premium ($)", "p_30_prem", 72000),
                ("45 Piezas Variadas ($)", "p_45_var", 94000),
                ("45 Piezas Premium ($)", "p_45_prem", 108000),
            ],
            columns=2
        )

        # 2. HOT ROLLS & BURGERS
        self.create_section_card(
            scrollable_frame,
            title="🔥 HOT ROLLS & HAMBURGUESA",
            fields=[
                ("Hot Rolls - Precio General ($)", "p_hotrolls", 20000),
                ("Hamburguesa con Papas Fritas ($)", "burguer_price", 18000),
            ],
            columns=2
        )

        # 3. EXTRAS
        self.create_section_card(
            scrollable_frame,
            title="🍤 EXTRAS & ACOMPAÑAMIENTOS",
            fields=[
                ("Porción de Rabas ($)", "p_rabas", 32000),
                ("Empanadas de Salmón (4u) ($)", "p_empanadas", 9500),
            ],
            columns=2
        )

    def create_section_card(self, parent, title, fields, columns=2):
        card = tk.LabelFrame(
            parent,
            text=f"  {title}  ",
            bg=BG_CARD,
            fg=ACCENT_PEACH,
            font=("Segoe UI", 10, "bold"),
            relief="solid",
            bd=1,
            padx=16,
            pady=12
        )
        card.pack(fill="x", padx=10, pady=8)

        grid_frame = tk.Frame(card, bg=BG_CARD)
        grid_frame.pack(fill="x")

        for idx, (label_text, var_key, default_val) in enumerate(fields):
            row = idx // columns
            col = (idx % columns) * 2

            lbl = tk.Label(
                grid_frame,
                text=label_text,
                bg=BG_CARD,
                fg=TEXT_WHITE,
                font=("Segoe UI", 9, "bold"),
                anchor="w"
            )
            lbl.grid(row=row, column=col, sticky="w", padx=(10 if col > 0 else 0, 8), pady=8)

            var = tk.StringVar(value=str(default_val))
            self.price_vars[var_key] = var

            entry = tk.Entry(
                grid_frame,
                textvariable=var,
                bg=BG_INPUT,
                fg="#FFFFFF",
                insertbackground="#FFFFFF",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                highlightthickness=1,
                highlightbackground=BORDER_COLOR,
                highlightcolor=ACCENT_ORANGE,
                justify="center",
                width=16
            )
            entry.grid(row=row, column=col + 1, sticky="w", padx=(0, 12), pady=8)

    def build_github_tab(self, parent):
        card = tk.LabelFrame(
            parent,
            text=" 🐙 Sincronización con GitHub ",
            bg=BG_CARD,
            fg=ACCENT_PEACH,
            font=("Segoe UI", 10, "bold"),
            relief="solid",
            bd=1,
            padx=20,
            pady=16
        )
        card.pack(fill="both", expand=True, padx=16, pady=16)

        banner_box = tk.Frame(card, bg="#1E2A3A", padx=12, pady=10, relief="solid", bd=1)
        banner_box.pack(fill="x", pady=(0, 14))

        has_tok = bool(self.github_token_var.get().strip())
        status_title = "✅ GitHub Desktop detectado y conectado (americansushibrc)" if has_tok else "💡 ¿Usás GitHub Desktop? ¡No necesitás Token manual!"
        status_desc = (
            "El sistema detectó automáticamente las credenciales de tu cuenta de GitHub.\n"
            "Con solo presionar '🚀 2. Guardar y Publicar en GitHub', los precios se suben a internet en 1 clic.\n"
            "(No necesitás configurar nada; todo funciona de manera 100% autónoma)."
        ) if has_tok else (
            "Si tenés tu carpeta en Documents/GitHub/americansushi, cambiá los precios y tocá\n"
            "'💾 1. Guardar en index.html'. Luego abrí GitHub Desktop y hacé clic en 'Commit to main' y 'Push origin'.\n"
            "¡El campo de token abajo es 100% opcional y podés dejarlo en blanco!"
        )

        tk.Label(
            banner_box,
            text=status_title,
            bg="#1E2A3A",
            fg=SUCCESS_GREEN,
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            banner_box,
            text=status_desc,
            bg="#1E2A3A",
            fg=TEXT_WHITE,
            font=("Segoe UI", 9),
            justify="left"
        ).pack(fill="x", pady=(4, 0))

        # Repositorio
        f_repo = tk.Frame(card, bg=BG_CARD)
        f_repo.pack(fill="x", pady=6)
        tk.Label(f_repo, text="Repositorio (usuario/repo):", bg=BG_CARD, fg=TEXT_WHITE, width=25, anchor="w").pack(side="left")
        tk.Entry(
            f_repo, 
            textvariable=self.github_repo_var, 
            bg=BG_INPUT, 
            fg=TEXT_WHITE, 
            relief="flat", 
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_ORANGE,
            font=("Segoe UI", 10)
        ).pack(side="left", fill="x", expand=True)

        # Rama
        f_branch = tk.Frame(card, bg=BG_CARD)
        f_branch.pack(fill="x", pady=6)
        tk.Label(f_branch, text="Rama (Branch):", bg=BG_CARD, fg=TEXT_WHITE, width=25, anchor="w").pack(side="left")
        tk.Entry(
            f_branch, 
            textvariable=self.github_branch_var, 
            bg=BG_INPUT, 
            fg=TEXT_WHITE, 
            relief="flat", 
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_ORANGE,
            font=("Segoe UI", 10)
        ).pack(side="left", fill="x", expand=True)

        # Token
        f_token = tk.Frame(card, bg=BG_CARD)
        f_token.pack(fill="x", pady=6)
        tk.Label(f_token, text="GitHub Token (Opcional):", bg=BG_CARD, fg=TEXT_WHITE, width=25, anchor="w").pack(side="left")
        self.token_entry = tk.Entry(
            f_token, 
            textvariable=self.github_token_var, 
            show="•", 
            bg=BG_INPUT, 
            fg=TEXT_WHITE, 
            relief="flat", 
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_ORANGE,
            font=("Segoe UI", 10)
        )
        self.token_entry.pack(side="left", fill="x", expand=True)

        self.show_token_var = tk.BooleanVar(value=False)
        def toggle_token():
            self.token_entry.config(show="" if self.show_token_var.get() else "•")
        
        tk.Checkbutton(
            f_token,
            text="Ver",
            variable=self.show_token_var,
            command=toggle_token,
            bg=BG_CARD,
            fg=TEXT_MUTED,
            selectcolor=BG_INPUT,
            activebackground=BG_CARD,
            activeforeground=TEXT_WHITE
        ).pack(side="left", padx=(8, 0))

        # Ubicación archivo index.html
        f_path = tk.Frame(card, bg=BG_CARD)
        f_path.pack(fill="x", pady=6)
        tk.Label(f_path, text="Ruta de index.html:", bg=BG_CARD, fg=TEXT_WHITE, width=25, anchor="w").pack(side="left")
        tk.Entry(
            f_path, 
            textvariable=self.index_path_var, 
            bg=BG_INPUT, 
            fg=TEXT_WHITE, 
            relief="flat", 
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_ORANGE,
            font=("Segoe UI", 9)
        ).pack(side="left", fill="x", expand=True)

        def browse_file():
            filename = filedialog.askopenfilename(
                title="Seleccionar index.html",
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
            )
            if filename:
                self.index_path_var.set(filename)
                self.load_prices_from_html()

        tk.Button(
            f_path,
            text="Buscar...",
            command=browse_file,
            bg="#2A3547",
            fg=TEXT_WHITE,
            font=("Segoe UI", 9),
            relief="flat",
            padx=10
        ).pack(side="left", padx=(8, 0))

        # Mensaje de commit opcional
        f_msg = tk.Frame(card, bg=BG_CARD)
        f_msg.pack(fill="x", pady=6)
        tk.Label(f_msg, text="Mensaje de Commit (opcional):", bg=BG_CARD, fg=TEXT_WHITE, width=25, anchor="w").pack(side="left")
        tk.Entry(
            f_msg, 
            textvariable=self.commit_msg_var, 
            bg=BG_INPUT, 
            fg=TEXT_WHITE, 
            relief="flat", 
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_ORANGE,
            font=("Segoe UI", 10)
        ).pack(side="left", fill="x", expand=True)

        # Botón Guardar Ajustes
        save_cfg_btn = tk.Button(
            card,
            text="💾 Recordar esta Configuración",
            command=self.save_admin_config,
            bg="#253245",
            fg=TEXT_WHITE,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            pady=8,
            cursor="hand2"
        )
        save_cfg_btn.pack(anchor="e", pady=(14, 0))


    def get_windows_github_token(self):
        try:
            import ctypes
            from ctypes import wintypes

            class CREDENTIAL(ctypes.Structure):
                _fields_ = [
                    ('Flags', wintypes.DWORD),
                    ('Type', wintypes.DWORD),
                    ('TargetName', wintypes.LPWSTR),
                    ('Comment', wintypes.LPWSTR),
                    ('LastWritten', wintypes.FILETIME),
                    ('CredentialBlobSize', wintypes.DWORD),
                    ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
                    ('Persist', wintypes.DWORD),
                    ('AttributeCount', wintypes.DWORD),
                    ('Attributes', ctypes.c_void_p),
                    ('TargetAlias', wintypes.LPWSTR),
                    ('UserName', wintypes.LPWSTR),
                ]

            advapi32 = ctypes.windll.advapi32
            CredReadW = advapi32.CredReadW
            CredReadW.argtypes = [wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
            CredReadW.restype = wintypes.BOOL

            targets = [
                'GitHub - https://api.github.com/americansushibrc',
                'git:https://github.com',
                'GitHub - https://api.github.com'
            ]
            for target in targets:
                p_cred = ctypes.POINTER(CREDENTIAL)()
                if CredReadW(target, 1, 0, ctypes.byref(p_cred)):
                    cred = p_cred.contents
                    raw_bytes = bytes(cred.CredentialBlob[:cred.CredentialBlobSize])
                    try:
                        tok = raw_bytes.decode('utf-8')
                    except Exception:
                        tok = raw_bytes.decode('utf-16le', errors='ignore')
                    if tok and (tok.startswith('ghp_') or tok.startswith('gho_') or tok.startswith('github_pat_') or len(tok) >= 30):
                        return tok.strip()
        except Exception:
            pass
        return None

    def get_git_executable(self):
        # 1. PATH
        import shutil, glob
        git_cmd = shutil.which("git")
        if git_cmd:
            return git_cmd

        # 2. GitHub Desktop
        gh_patterns = [
            os.path.expandvars(r"%LOCALAPPDATA%\GitHubDesktop\app-*\resources\app\git\cmd\git.exe"),
            r"C:\Users\nicol\AppData\Local\GitHubDesktop\app-3.6.10\resources\app\git\cmd\git.exe",
            r"C:\Program Files\Git\cmd\git.exe",
            r"C:\Program Files (x86)\Git\cmd\git.exe"
        ]
        for pattern in gh_patterns:
            matches = glob.glob(pattern)
            if matches:
                return matches[-1]
            if os.path.exists(pattern):
                return pattern
        return "git"

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        self.log_text.config(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def open_local_preview(self):
        filepath = self.index_path_var.get().strip()
        if os.path.exists(filepath):
            webbrowser.open_new_tab(f"file:///{os.path.abspath(filepath)}")
            self.log(f"🌐 Abriendo {os.path.basename(filepath)} en tu navegador predeterminado.")
        else:
            messagebox.showerror("Error", f"No se encontró el archivo: {filepath}")

    def load_admin_config(self):
        saved_token = ""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved_token = data.get("github_token", "").strip()
                    self.github_token_var.set(saved_token)
                    self.github_repo_var.set(data.get("github_repo", "americansushibrc/americansushi"))
                    self.github_branch_var.set(data.get("github_branch", "main"))
                    saved_path = data.get("index_path", INDEX_FILE)
                    if os.path.exists(saved_path):
                        self.index_path_var.set(saved_path)
            except Exception as e:
                print("Error al leer admin_config.json:", e)

        # Si no había token guardado manualmente, buscar el token de GitHub Desktop en Windows
        if not self.github_token_var.get().strip():
            auto_tok = self.get_windows_github_token()
            if auto_tok:
                self.github_token_var.set(auto_tok)

    def save_admin_config(self):
        data = {
            "github_token": self.github_token_var.get().strip(),
            "github_repo": self.github_repo_var.get().strip(),
            "github_branch": self.github_branch_var.get().strip(),
            "index_path": self.index_path_var.get().strip()
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.log("✅ Configuración guardada correctamente.")
            messagebox.showinfo("Configuración", "Ajustes guardados con éxito.")
        except Exception as e:
            self.log(f"❌ Error al guardar configuración: {e}")

    def load_prices_from_html(self):
        filepath = self.index_path_var.get().strip()
        if not os.path.exists(filepath):
            if os.path.exists(INDEX_FILE):
                filepath = INDEX_FILE
                self.index_path_var.set(filepath)
            else:
                self.log(f"⚠️ Archivo no encontrado en: {filepath}")
                return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            match = re.search(r"prices:\s*\{([^}]+)\}", content)
            if match:
                block = match.group(1)
                found = 0
                for line in block.splitlines():
                    m = re.search(r"['\"]([^'\"]+)['\"]\s*:\s*([0-9]+)", line)
                    if m:
                        key = m.group(1)
                        val = m.group(2)
                        if key in self.price_vars:
                            self.price_vars[key].set(val)
                            found += 1
                self.log(f"✅ Se cargaron exitosamente {found} precios desde {os.path.basename(filepath)}.")
            else:
                self.log("⚠️ No se encontró el bloque DEFAULT_CONFIG.prices en index.html.")
        except Exception as e:
            self.log(f"❌ Error al leer index.html: {e}")

    def format_currency_ar(self, val):
        s = f"{val:,}".replace(",", ".")
        return f"${s}"

    def update_html_content(self, html_content, prices):
        new_version = f"v_{int(time.time())}"
        
        # 1. Actualizar DEFAULT_CONFIG.configVersion
        if "configVersion:" in html_content:
            html_content = re.sub(
                r"configVersion:\s*['\"][^'\"]+['\"]",
                f"configVersion: '{new_version}'",
                html_content
            )
        else:
            html_content = re.sub(
                r"const DEFAULT_CONFIG = \{",
                f"const DEFAULT_CONFIG = {{\n    configVersion: '{new_version}',",
                html_content
            )
        
        # 2. Actualizar valores en DEFAULT_CONFIG.prices
        for key, val in prices.items():
            html_content = re.sub(
                rf"(['\"]{key}['\"]\s*:\s*)[0-9]+",
                rf"\g<1>{val}",
                html_content
            )
            html_content = re.sub(
                rf'(id="cms_{key}"\s+value=")[0-9]+(")',
                rf"\g<1>{val}\g<2>",
                html_content
            )
            html_content = re.sub(
                rf'(value=")[0-9]+("\s+id="cms_{key}")',
                rf"\g<1>{val}\g<2>",
                html_content
            )
            
        # 3. Mapeo para ítems visuales en el HTML y botones addToCart
        item_mappings = [
            ("Tabla 12 Piezas Variadas", r"Tabla 12 Piezas Variadas", prices.get("p_12_var")),
            ("Tabla 12 Piezas Premium", r"Tabla 12 Piezas Premium", prices.get("p_12_prem")),
            ("Tabla 20 Piezas Variadas", r"Tabla 20 Piezas Variadas", prices.get("p_20_var")),
            ("Tabla 20 Piezas Premium", r"Tabla 20 Piezas Premium", prices.get("p_20_prem")),
            ("Tabla 30 Piezas Variadas", r"Tabla 30 Piezas Variadas", prices.get("p_30_var")),
            ("Tabla 30 Piezas Premium", r"Tabla 30 Piezas Premium", prices.get("p_30_prem")),
            ("Tabla 45 Piezas Variadas", r"Tabla 45 Piezas Variadas", prices.get("p_45_var")),
            ("Tabla 45 Piezas Premium", r"Tabla 45 Piezas Premium", prices.get("p_45_prem")),
            ("Hot Roll Salmón (8p)", r"Hot Roll Salmón \(8p\)", prices.get("p_hotrolls")),
            ("Hot Roll Langostinos (8p)", r"Hot Roll Langostinos \(8p\)", prices.get("p_hotrolls")),
            ("Hot Roll Kanikama (8p)", r"Hot Roll Kanikama \(8p\)", prices.get("p_hotrolls")),
            ("Hot Roll Atún (8p)", r"Hot Roll Atún \(8p\)", prices.get("p_hotrolls")),
            ("Hot Roll Vegetariano (8p)", r"Hot Roll Vegetariano \(8p\)", prices.get("p_hotrolls")),
            ("Hamburguesa con Papas Fritas", r"Hamburguesa con Papas Fritas", prices.get("burguer_price")),
            ("Porción de Rabas", r"Porción de Rabas", prices.get("p_rabas")),
            ("Empanadas de Salmón (4u)", r"Empanadas de Salmón \(4u\)", prices.get("p_empanadas")),
        ]
        
        for name_clean, name_regex, price in item_mappings:
            if price is None:
                continue
            formatted_price = self.format_currency_ar(price)
            
            pair_pattern = rf'(<span>)[0-9$. ]+(</span>\s*<button class="add-item-btn" onclick="addToCart\(\'{name_regex}\',\s*)[0-9]+(\)">\+ Pedir</button>)'
            if re.search(pair_pattern, html_content):
                html_content = re.sub(
                    pair_pattern,
                    rf'\g<1>{formatted_price}\g<2>{price}\g<3>',
                    html_content
                )
            else:
                html_content = re.sub(
                    rf"(addToCart\('{name_regex}',\s*)[0-9]+(\))",
                    rf"\g<1>{price}\g<2>",
                    html_content
                )

        return html_content, new_version

    def get_validated_prices(self):
        prices = {}
        for key, var in self.price_vars.items():
            val_str = var.get().strip().replace(".", "").replace("$", "")
            if not val_str.isdigit():
                messagebox.showerror("Error de Validación", f"El valor para '{key}' debe ser un número entero.")
                return None
            prices[key] = int(val_str)
        return prices

    def save_local_only(self):
        prices = self.get_validated_prices()
        if not prices:
            return False

        filepath = self.index_path_var.get().strip()
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"No se encontró el archivo: {filepath}")
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            updated_content, version = self.update_html_content(content, prices)

            # Guardar archivo actualizado
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(updated_content)

            self.log(f"💾 Guardado exitoso en {os.path.basename(filepath)} (Versión {version}).")
            messagebox.showinfo(
                "¡Precios Guardados!", 
                f"Los precios se actualizaron con éxito en {os.path.basename(filepath)}.\n\n"
                f"Nueva versión generada: {version}\n\n"
                f"👉 Si usás GitHub Desktop, ya podés abrirlo y hacer 'Commit' y 'Push' para que se suba a internet."
            )
            return True
        except Exception as e:
            self.log(f"❌ Error al guardar: {e}")
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")
            return False

    def save_and_publish(self):
        if not self.save_local_only():
            return

        token = self.github_token_var.get().strip() or self.get_windows_github_token()
        repo = self.github_repo_var.get().strip() or "americansushibrc/americansushi"
        branch = self.github_branch_var.get().strip() or "main"
        filepath = self.index_path_var.get().strip()

        commit_msg = self.commit_msg_var.get().strip()
        if not commit_msg:
            commit_msg = f"Actualización de precios: {datetime.now().strftime('%d/%m/%Y %H:%M')}"

        self.log(f"🚀 Iniciando sincronización con GitHub ({repo})...")

        # 1. Si existe carpeta .git local y Git CLI disponible
        repo_dir = os.path.dirname(os.path.abspath(filepath))
        git_bin = self.get_git_executable()
        git_success = False

        if os.path.exists(os.path.join(repo_dir, ".git")):
            try:
                self.log(f"Ejecutando Git ({os.path.basename(git_bin)})...")
                subprocess.run([git_bin, "add", "index.html"], cwd=repo_dir, capture_output=True, text=True)
                subprocess.run([git_bin, "commit", "-m", commit_msg], cwd=repo_dir, capture_output=True, text=True)
                
                # Push con autenticación directa si tenemos token (evita popup modal bloqueante)
                if token:
                    push_url = f"https://x-access-token:{token}@github.com/{repo}.git"
                    push_res = subprocess.run([git_bin, "push", push_url, branch], cwd=repo_dir, capture_output=True, text=True)
                    if push_res.returncode == 0:
                        subprocess.run([git_bin, "fetch", "origin", branch], cwd=repo_dir, capture_output=True, text=True)
                        git_success = True
                else:
                    push_res = subprocess.run([git_bin, "push", "origin", branch], cwd=repo_dir, capture_output=True, text=True)
                    if push_res.returncode == 0 or "Everything up-to-date" in push_res.stderr or "Everything up-to-date" in push_res.stdout:
                        git_success = True

                if git_success:
                    self.log("🎉 ¡Publicación exitosa vía Git!")
                    messagebox.showinfo("Publicado en GitHub", f"¡Los cambios fueron enviados a GitHub ({branch}) con éxito!\n\nEn 1 a 2 minutos GitHub Pages se actualizará automáticamente.")
                    return
                else:
                    self.log(f"Git push detalle: {push_res.stdout} {push_res.stderr}")
            except Exception as e:
                self.log(f"Aviso de Git local: {e}")

        # 2. Vía GitHub API directa (si hay token)
        if token:
            self.publish_via_github_api(filepath, repo, branch, token, commit_msg)
        else:
            msg = (
                "¡Los precios ya fueron guardados en tu index.html local!\n\n"
                "Para publicarlos en GitHub:\n"
                "1. Abrí tu programa 'GitHub Desktop'.\n"
                "2. Hacé clic en 'Commit to main' y luego en 'Push origin'.\n\n"
                "¡En 1 minuto se actualizará la web para todos tus clientes!"
            )
            messagebox.showinfo("Listo para publicar", msg)

    def publish_via_github_api(self, filepath, repo, branch, token, commit_msg):
        try:
            with open(filepath, "rb") as f:
                file_bytes = f.read()

            base64_content = base64.b64encode(file_bytes).decode("utf-8")
            api_url = f"https://api.github.com/repos/{repo}/contents/index.html"

            req_get = urllib.request.Request(
                api_url + f"?ref={branch}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "AmericanSushiAdminPython"
                }
            )
            
            sha = None
            try:
                with urllib.request.urlopen(req_get) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    sha = res_data.get("sha")
            except urllib.error.HTTPError as he:
                if he.code != 404:
                    raise he

            payload = {
                "message": commit_msg,
                "content": base64_content,
                "branch": branch
            }
            if sha:
                payload["sha"] = sha

            req_put = urllib.request.Request(
                api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "Content-Type": "application/json",
                    "User-Agent": "AmericanSushiAdminPython"
                },
                method="PUT"
            )

            with urllib.request.urlopen(req_put) as response:
                if response.status in (200, 201):
                    self.log(f"🎉 ¡Publicación exitosa en GitHub ({repo} / {branch})!")
                    self.save_admin_config()
                    messagebox.showinfo(
                        "Publicado con Éxito",
                        f"¡Los precios se publicaron en GitHub ({repo})!\n\n"
                        f"Cualquier cliente que abra la página desde su celular verá los nuevos precios de inmediato."
                    )
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            self.log(f"❌ Error de GitHub API ({e.code}): {err_body}")
            messagebox.showerror("Error de GitHub", f"No se pudo publicar (Código {e.code}):\n{err_body}")
        except Exception as e:
            self.log(f"❌ Error de conexión: {e}")
            messagebox.showerror("Error", f"Ocurrió un error al conectar con GitHub:\n{e}")

def main():
    root = tk.Tk()
    app = SushiAdminApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
