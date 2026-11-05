import os
from pathlib import Path

# Тесты читают отдельный env-файл, а не src/bots_place/config/.env
os.environ["BOTS_PLACE_ENV_FILE"] = str(Path(__file__).with_name("test.env"))
