import platform
import psutil

def get_system_info():
    # Operating System Information
    print("Système d'exploitation :")
    print(f"Nom de l'OS: {platform.system()}")
    print(f"Version de l'OS: {platform.version()}")

    # Processor Information
    print(\nProcesseur :)\n    print(f"Nom du processeur: {platform.processor()}")
    print(f"Nombre de cœurs physiques: {psutil.cpu_count(logical=False)}")
    print(f"Nombre total de cœurs (y compris les threads): {psutil.cpu_count()}\n")

    # Memory Information
    memory_info = psutil.virtual_memory()
    print(\nMémoire :)\n    print(f"Totaux : {memory_info.total / (1024 ** 3)} GB")
    print(f"Libres : {memory_info.available / (1024 ** 3):.2f} GB")

    # Disk Information
    disk_usage = psutil.disk_usage('/')\n    print(\nDisque :)\n    print(f"Espace total: {disk_usage.total / (1024**3)} GB")\n    print(f"Espace libre: {disk_usage.free / (1024**3):.2f} GB")

if __name__ == \"__main__\":\n    get_system_info()