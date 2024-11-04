import logging
import json
import os


# Config path
CONFIG_PATH = 'configs/config.json'
UI_CONFIG_PATH = 'configs/ui_config.json'
TTS_CONFIG_PATH = 'configs/tts_config.json'


def load_config():
    with open(CONFIG_PATH, 'r') as config_file:
        config = json.load(config_file)
    return config


def load_ui_config():
    with open(UI_CONFIG_PATH, 'r') as config_file:
        config = json.load(config_file)
    return config


def load_tts_config():
    with open(TTS_CONFIG_PATH, 'r') as config_file:
        config = json.load(config_file)
    return config


# Creating a log dir for a single log
log_dir = "log"
os.makedirs(log_dir, exist_ok=True) 
log_file = os.path.join(log_dir, "last_run.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(threadName)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="w")
    ]
)

logger = logging.getLogger("")
