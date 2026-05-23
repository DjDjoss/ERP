import argparse
import json
import platform
import queue
import re
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from tkinter import BOTH, LEFT, RIGHT, X, filedialog, messagebox, Tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


APP_TITLE = "Diagnostic PC"


def run_powershell(script: str):
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        script,
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        error_text = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(error_text or "Commande PowerShell échouée.")
    output = result.stdout.strip()
    return json.loads(output) if output else None


def ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def format_bytes(value):
    if value in (None, "", 0, "0"):
        return "0 B"
    try:
        size = float(value)
    except (TypeError, ValueError):
        return str(value)
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"


def format_frequency(mhz):
    if not mhz:
        return "Inconnu"
    try:
        ghz = float(mhz) / 1000
    except (TypeError, ValueError):
        return str(mhz)
    return f"{ghz:.2f} GHz"


def format_datetime(value):
    if not value:
        return "Inconnu"
    value = str(value)
    match = re.match(r"^/Date\((\d+)\)/$", value)
    if match:
        try:
            parsed = datetime.fromtimestamp(int(match.group(1)) / 1000)
            return parsed.strftime("%d/%m/%Y %H:%M:%S")
        except (TypeError, ValueError, OSError):
            return value
    if "+" in value:
        value = value.split("+", 1)[0]
    if "." in value:
        base, frac = value.split(".", 1)
        frac = "".join(ch for ch in frac if ch.isdigit())[:6]
        value = f"{base}.{frac}" if frac else base
    for fmt in ("%Y%m%d%H%M%S.%f", "%Y%m%d%H%M%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime("%d/%m/%Y %H:%M:%S")
        except ValueError:
            continue
    return str(value)


def ps_json(query: str):
    script = f"{query} | ConvertTo-Json -Depth 5 -Compress"
    return run_powershell(script)


def build_specs():
    os_info = ps_json(
        "Get-CimInstance Win32_OperatingSystem | "
        "Select-Object Caption, Version, BuildNumber, OSArchitecture, LastBootUpTime"
    ) or {}
    system_info = ps_json(
        "Get-CimInstance Win32_ComputerSystem | "
        "Select-Object Manufacturer, Model, TotalPhysicalMemory, UserName"
    ) or {}
    processor = ps_json(
        "Get-CimInstance Win32_Processor | "
        "Select-Object Name, Manufacturer, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed"
    ) or {}
    bios = ps_json(
        "Get-CimInstance Win32_BIOS | "
        "Select-Object Manufacturer, SMBIOSBIOSVersion, ReleaseDate, SerialNumber"
    ) or {}
    motherboard = ps_json(
        "Get-CimInstance Win32_BaseBoard | "
        "Select-Object Manufacturer, Product, SerialNumber"
    ) or {}
    gpus = ensure_list(
        ps_json(
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name, AdapterRAM, DriverVersion, VideoProcessor, "
            "CurrentHorizontalResolution, CurrentVerticalResolution"
        )
    )
    physical_memory = ensure_list(
        ps_json(
            "Get-CimInstance Win32_PhysicalMemory | "
            "Select-Object Manufacturer, Capacity, Speed, PartNumber, BankLabel"
        )
    )
    disk_drives = ensure_list(
        ps_json(
            "Get-CimInstance Win32_DiskDrive | "
            "Select-Object Model, MediaType, Size, InterfaceType, SerialNumber"
        )
    )
    logical_disks = ensure_list(
        ps_json(
            "Get-CimInstance Win32_LogicalDisk | "
            "Select-Object DeviceID, VolumeName, FileSystem, Size, FreeSpace, DriveType"
        )
    )
    network_adapters = ensure_list(
        ps_json(
            "Get-CimInstance Win32_NetworkAdapterConfiguration -Filter \"IPEnabled = True\" | "
            "Select-Object Description, MACAddress, IPAddress, DefaultIPGateway, DHCPEnabled"
        )
    )

    total_ram = format_bytes(system_info.get("TotalPhysicalMemory"))
    ram_modules = []
    for module in physical_memory:
        ram_modules.append(
            {
                "Banque": module.get("BankLabel") or "Inconnue",
                "Capacite": format_bytes(module.get("Capacity")),
                "Frequence": f"{module.get('Speed', 'Inconnue')} MHz" if module.get("Speed") else "Inconnue",
                "Fabricant": module.get("Manufacturer") or "Inconnu",
                "Reference": (module.get("PartNumber") or "").strip() or "Inconnue",
            }
        )

    gpu_items = []
    for gpu in gpus:
        resolution = "Inconnue"
        if gpu.get("CurrentHorizontalResolution") and gpu.get("CurrentVerticalResolution"):
            resolution = (
                f"{gpu['CurrentHorizontalResolution']} x {gpu['CurrentVerticalResolution']}"
            )
        gpu_items.append(
            {
                "Nom": gpu.get("Name") or "Inconnu",
                "Memoire": format_bytes(gpu.get("AdapterRAM")),
                "Pilote": gpu.get("DriverVersion") or "Inconnu",
                "Processeur video": gpu.get("VideoProcessor") or "Inconnu",
                "Resolution": resolution,
            }
        )

    physical_disk_items = []
    for disk in disk_drives:
        physical_disk_items.append(
            {
                "Modele": disk.get("Model") or "Inconnu",
                "Type": disk.get("MediaType") or "Inconnu",
                "Interface": disk.get("InterfaceType") or "Inconnue",
                "Taille": format_bytes(disk.get("Size")),
                "Serie": (disk.get("SerialNumber") or "").strip() or "Inconnue",
            }
        )

    logical_disk_items = []
    for disk in logical_disks:
        drive_type = disk.get("DriveType")
        drive_label = "Local" if drive_type == 3 else str(drive_type)
        logical_disk_items.append(
            {
                "Lecteur": disk.get("DeviceID") or "Inconnu",
                "Nom": disk.get("VolumeName") or "Sans nom",
                "Type": drive_label,
                "Format": disk.get("FileSystem") or "Inconnu",
                "Taille": format_bytes(disk.get("Size")),
                "Libre": format_bytes(disk.get("FreeSpace")),
            }
        )

    network_items = []
    for adapter in network_adapters:
        ip_addresses = adapter.get("IPAddress") or []
        gateways = adapter.get("DefaultIPGateway") or []
        network_items.append(
            {
                "Nom": adapter.get("Description") or "Inconnu",
                "MAC": adapter.get("MACAddress") or "Inconnue",
                "IP": ", ".join(ip_addresses) if ip_addresses else "Inconnue",
                "Passerelle": ", ".join(gateways) if gateways else "Inconnue",
                "DHCP": "Oui" if adapter.get("DHCPEnabled") else "Non",
            }
        )

    specs = {
        "Resume": {
            "Nom du PC": platform.node() or "Inconnu",
            "Systeme": os_info.get("Caption") or platform.platform(),
            "Version": f"{os_info.get('Version', 'Inconnue')} (build {os_info.get('BuildNumber', 'N/A')})",
            "Architecture": os_info.get("OSArchitecture") or platform.machine(),
            "Fabricant": system_info.get("Manufacturer") or "Inconnu",
            "Modele": system_info.get("Model") or "Inconnu",
            "Utilisateur": system_info.get("UserName") or "Inconnu",
            "Dernier demarrage": format_datetime(os_info.get("LastBootUpTime")),
            "RAM totale": total_ram,
        },
        "CPU": {
            "Nom": processor.get("Name") or "Inconnu",
            "Fabricant": processor.get("Manufacturer") or "Inconnu",
            "Coeurs": processor.get("NumberOfCores") or "Inconnu",
            "Threads": processor.get("NumberOfLogicalProcessors") or "Inconnu",
            "Frequence max": format_frequency(processor.get("MaxClockSpeed")),
        },
        "Carte mere et BIOS": {
            "Carte mere": {
                "Fabricant": motherboard.get("Manufacturer") or "Inconnu",
                "Modele": motherboard.get("Product") or "Inconnu",
                "Serie": motherboard.get("SerialNumber") or "Inconnue",
            },
            "BIOS": {
                "Fabricant": bios.get("Manufacturer") or "Inconnu",
                "Version": bios.get("SMBIOSBIOSVersion") or "Inconnue",
                "Date": format_datetime(bios.get("ReleaseDate")),
                "Serie": bios.get("SerialNumber") or "Inconnue",
            },
        },
        "Memoire RAM": {
            "Total": total_ram,
            "Barrettes": ram_modules,
        },
        "Cartes graphiques": gpu_items,
        "Disques physiques": physical_disk_items,
        "Volumes logiques": logical_disk_items,
        "Reseau": network_items,
    }
    return specs


def flatten_to_text(specs):
    lines = []

    def walk(title, value, indent=0):
        prefix = " " * indent
        if isinstance(value, dict):
            lines.append(f"{prefix}{title}")
            for key, sub_value in value.items():
                walk(key, sub_value, indent + 2)
        elif isinstance(value, list):
            lines.append(f"{prefix}{title}")
            if not value:
                lines.append(f"{prefix}  Aucune donnee")
            for index, item in enumerate(value, start=1):
                if isinstance(item, (dict, list)):
                    walk(f"Element {index}", item, indent + 2)
                else:
                    lines.append(f"{prefix}  - {item}")
        else:
            lines.append(f"{prefix}{title}: {value}")

    for section, content in specs.items():
        walk(section, content)
        lines.append("")
    return "\n".join(lines).strip()


class SpecsApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.minsize(900, 620)
        self.root.geometry("1080x760")

        self.style = ttk.Style()
        if "vista" in self.style.theme_names():
            self.style.theme_use("vista")

        self.notebook = None
        self.status_var = None
        self.summary_labels = {}
        self.tab_widgets = {}
        self.specs = {}
        self.queue = queue.Queue()
        self.loading = False

        self.build_ui()
        self.center_window()
        self.present_window()
        self.root.after(150, self.refresh_specs)

    def build_ui(self):
        main = ttk.Frame(self.root, padding=14)
        main.pack(fill=BOTH, expand=True)

        header = ttk.Frame(main)
        header.pack(fill=X)

        title = ttk.Label(header, text="Spécifications de l'ordinateur", font=("Segoe UI", 18, "bold"))
        title.pack(side=LEFT)

        action_bar = ttk.Frame(header)
        action_bar.pack(side=RIGHT)

        ttk.Button(action_bar, text="Rafraichir", command=self.refresh_specs).pack(side=LEFT, padx=(0, 8))
        ttk.Button(action_bar, text="Copier", command=self.copy_specs).pack(side=LEFT, padx=(0, 8))
        ttk.Button(action_bar, text="Exporter JSON", command=self.export_specs).pack(side=LEFT)

        summary = ttk.LabelFrame(main, text="Résumé rapide", padding=12)
        summary.pack(fill=X, pady=(12, 12))

        summary_keys = [
            "Nom du PC",
            "Systeme",
            "Modele",
            "CPU",
            "RAM totale",
            "Dernier demarrage",
        ]
        for index, key in enumerate(summary_keys):
            row = index // 2
            col = index % 2
            card = ttk.Frame(summary, padding=6)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            summary.columnconfigure(col, weight=1)
            ttk.Label(card, text=key, font=("Segoe UI", 9, "bold")).pack(anchor="w")
            value_label = ttk.Label(card, text="-", wraplength=460, justify=LEFT)
            value_label.pack(anchor="w", pady=(2, 0))
            self.summary_labels[key] = value_label

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=BOTH, expand=True)

        self.status_var = ttk.Label(main, text="Prêt.", anchor="w")
        self.status_var.pack(fill=X, pady=(10, 0))

    def set_status(self, text):
        self.status_var.config(text=text)
        self.root.update_idletasks()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width() or 1080
        height = self.root.winfo_height() or 760
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max((screen_width - width) // 2, 0)
        y = max((screen_height - height) // 2, 0)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def present_window(self):
        # Force a visible foreground launch, then restore normal stacking.
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self.root.after(1200, lambda: self.root.attributes("-topmost", False))

    def refresh_specs(self):
        if self.loading:
            return
        self.loading = True
        self.set_status("Collecte des informations système en cours...")
        self.clear_tabs_with_message("Chargement des spécifications en cours...")
        worker = threading.Thread(target=self._collect_specs, daemon=True)
        worker.start()
        self.root.after(100, self.poll_queue)

    def _collect_specs(self):
        try:
            self.queue.put(("success", build_specs()))
        except Exception as exc:
            self.queue.put(("error", str(exc)))

    def poll_queue(self):
        try:
            status, payload = self.queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self.poll_queue)
            return

        self.loading = False
        if status == "success":
            self.specs = payload
            self.render_specs()
            self.set_status("Collecte terminée.")
            return

        self.set_status("Erreur pendant la collecte.")
        self.clear_tabs_with_message("Impossible de récupérer les spécifications.")
        messagebox.showerror(APP_TITLE, f"Impossible de récupérer les spécifications.\n\n{payload}")

    def clear_tabs_with_message(self, message):
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        placeholder = ttk.Frame(self.notebook, padding=16)
        label = ttk.Label(placeholder, text=message, font=("Segoe UI", 11))
        label.pack(anchor="center", expand=True)
        self.notebook.add(placeholder, text="Chargement")

    def render_specs(self):
        summary = self.specs.get("Resume", {})
        self.summary_labels["Nom du PC"].config(text=summary.get("Nom du PC", "-"))
        self.summary_labels["Systeme"].config(text=summary.get("Systeme", "-"))
        self.summary_labels["Modele"].config(text=summary.get("Modele", "-"))
        self.summary_labels["CPU"].config(text=self.specs.get("CPU", {}).get("Nom", "-"))
        self.summary_labels["RAM totale"].config(text=summary.get("RAM totale", "-"))
        self.summary_labels["Dernier demarrage"].config(text=summary.get("Dernier demarrage", "-"))

        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        self.tab_widgets.clear()

        for section, content in self.specs.items():
            frame = ttk.Frame(self.notebook, padding=10)
            text = ScrolledText(frame, wrap="word", font=("Consolas", 10), height=20)
            text.pack(fill=BOTH, expand=True)
            text.insert("1.0", self.format_section(section, content))
            text.config(state="disabled")
            self.notebook.add(frame, text=section)
            self.tab_widgets[section] = text

    def format_section(self, title, content):
        return flatten_to_text({title: content})

    def copy_specs(self):
        if not self.specs:
            return
        text = flatten_to_text(self.specs)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.set_status("Les spécifications ont été copiées dans le presse-papiers.")

    def export_specs(self):
        if not self.specs:
            return
        filename = filedialog.asksaveasfilename(
            title="Exporter les spécifications",
            defaultextension=".json",
            filetypes=[("Fichier JSON", "*.json"), ("Tous les fichiers", "*.*")],
            initialfile="specifications_pc.json",
        )
        if not filename:
            return
        with open(filename, "w", encoding="utf-8") as handle:
            json.dump(self.specs, handle, ensure_ascii=False, indent=2)
        self.set_status(f"Export terminé : {filename}")


def main():
    parser = argparse.ArgumentParser(description="Affiche les spécifications du PC.")
    parser.add_argument("--json", action="store_true", help="Affiche les spécifications au format JSON dans la console.")
    args = parser.parse_args()

    if args.json:
        specs = build_specs()
        print(json.dumps(specs, ensure_ascii=False, indent=2))
        return

    root = Tk()
    SpecsApp(root)
    root.mainloop()


if __name__ == "__main__":
    if shutil.which("powershell") is None:
        sys.exit("PowerShell est requis pour exécuter cette application.")
    main()
