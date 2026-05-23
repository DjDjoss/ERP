#!/usr/bin/env python3
import platform
import psutil

# Function to get system specifications

def get_system_specifications():
    specs = {
        'System': platform.system(),
        'Node Name': platform.node(),
        'Release': platform.release(),
        'Version': platform.version(),
        'Machine': platform.machine(),
        'Processor': platform.processor()
    }

    # Adding CPU information
    cpu_info = {
        'Physical Cores': psutil.cpu_count(logical=False),
        'Total Cores': psutil.cpu_count(logical=True),
        'Max Frequency (MHz)': psutil.cpu_freq().max,
        'CPU Usage (%)': psutil.cpu_percent()
    }

    # Adding Memory Information
    memory_info = {
        'Total Physical Memory (GB)': round(psutil.virtual_memory().total / (1024.0 ** 3), 2),
        'Available Physical Memory (GB)': round(psutil.virtual_memory().available / (1024.0 ** 3), 2),
        'Memory Usage (%)': psutil.virtual_memory().percent
    }

    # Adding Disk Information
    disk_info = {
        'Total Disk Space (GB)': round(psutil.disk_usage('/').total / (1024.0 ** 3), 2),
        'Used Disk Space (GB)': round(psutil.disk_usage('/').used / (1024.0 ** 3), 2),
        'Free Disk Space (GB)': round(psutil.disk_usage('/').free / (1024.0 ** 3), 2)
    }

    return specs, cpu_info, memory_info, disk_info
