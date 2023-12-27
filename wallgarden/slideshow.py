import subprocess
import os
import shutil
import sys

from wallgarden.config import PROJECT_PATH
from wallgarden.utils import ESCAPE_FLATPAK

SYSTEMD_USER_DIR = os.path.expanduser('~/.config/systemd/user/')
PYTHON_INTERP_PATH = sys.executable
DEFAULT_TIMER_MINUTES = '10'
SERVICE_NAME = 'wallgarden.service'
TIMER_NAME = 'wallgarden.timer'
TEMPLATE_SUFFIX = '.template'
TEMPLATE_DIR = os.path.join(PROJECT_PATH,'service')
CLI_PATH = os.path.join(PROJECT_PATH, 'cli.py')

SERVICE_TEMPLATE_NAME = SERVICE_NAME + TEMPLATE_SUFFIX
SERVICE_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, SERVICE_TEMPLATE_NAME)
TIMER_TEMPLATE_NAME = TIMER_NAME + TEMPLATE_SUFFIX
TIMER_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, TIMER_TEMPLATE_NAME)
SERVICE_SRC_PATH = os.path.join(TEMPLATE_DIR, SERVICE_NAME)
TIMER_SRC_PATH = os.path.join(TEMPLATE_DIR, TIMER_NAME)
SERVICE_DEST_PATH = os.path.join(SYSTEMD_USER_DIR, SERVICE_NAME)
TIMER_DEST_PATH = os.path.join(SYSTEMD_USER_DIR, TIMER_NAME)


def prepare_service_template():
    if not os.path.exists(SERVICE_SRC_PATH):
        with open(SERVICE_TEMPLATE_PATH, 'r') as template_file:
            content = template_file.read()

        content = content.replace('__sys.executable__', sys.executable)
        content = content.replace('__wallgarden.cli__', CLI_PATH)

        with open(SERVICE_SRC_PATH, 'w') as service_file:
            service_file.write(content)

def prepare_timer_template(minutes):
    if not os.path.exists(TIMER_SRC_PATH):
        with open(TIMER_TEMPLATE_PATH, 'r') as template_file:
            content = template_file.read()

        content = content.replace('__minutes__', minutes)

        with open(TIMER_SRC_PATH, 'w') as timer_file:
            timer_file.write(content)

def install_timer_files(minutes = None):
    if minutes is None:
        if not os.path.exists(TIMER_SRC_PATH):
            prepare_timer_template(DEFAULT_TIMER_MINUTES)
        if not os.path.exists(TIMER_DEST_PATH):
            shutil.copy(TIMER_SRC_PATH, TIMER_DEST_PATH)
    else:
        prepare_timer_template(minutes)
        shutil.copy(TIMER_SRC_PATH, TIMER_DEST_PATH)

def install_service_files():
    # Ensure the systemd user directory exists
    os.makedirs(SYSTEMD_USER_DIR, exist_ok=True)

    if not os.path.exists(SERVICE_SRC_PATH):
        prepare_service_template()
    if not os.path.exists(SERVICE_DEST_PATH):
        shutil.copy(SERVICE_SRC_PATH, SERVICE_DEST_PATH)

    

def is_service_active():
    try:
        result = subprocess.run(ESCAPE_FLATPAK + ["systemctl", "--user", "is-active", "wallgarden.timer"], check=True, capture_output=True, text=True)
        return "active" in result.stdout
    except subprocess.CalledProcessError:
        return False


def toggle_service(enable):
    # First, ensure the service files are in place and the service is enabled
    install_service_files()
    install_timer_files()

    subprocess.run(ESCAPE_FLATPAK + ["systemctl", "--user", "enable", "wallgarden.timer"])

    if enable:
        subprocess.run(ESCAPE_FLATPAK + ["systemctl", "--user", "start", "wallgarden.timer"])
    else:
        subprocess.run(ESCAPE_FLATPAK + ["systemctl", "--user", "stop", "wallgarden.timer"])


def reload_systemd_daemon():
    subprocess.run(ESCAPE_FLATPAK + ["systemctl", "--user", "daemon-reload"])
