from pathlib import Path

import yaml
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"

load_dotenv(BASE_DIR / ".env")

with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)


def get_site_config(site):
    if site not in config["sites"]:
        available_sites = ", ".join(config["sites"].keys())
        raise ValueError(f"Unknown site '{site}'. Available sites: {available_sites}")
    return config["sites"][site]
