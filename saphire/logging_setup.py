import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from .settings import settings

COLORS = {"INFO":"\033[94m","ERROR":"\033[91m","LOGGED":"\033[38;5;214m","WARNING":"\033[93m","SUCCESS":"\033[92m"}
logging.addLevelName(25,"LOGGED")
class Formatter(logging.Formatter):
    def format(self, record):
        try: now = datetime.now(ZoneInfo(settings.log_timezone))
        except Exception: now = datetime.now().astimezone()
        stamp = now.strftime("%I:%M%p").lstrip("0").lower()
        prefix = f"[{stamp}] [+] {record.levelname} -"
        if sys.stdout.isatty(): prefix = COLORS.get(record.levelname,"") + prefix + "\033[0m"
        return prefix + " " + record.getMessage()
def configure_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(Formatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
def logged(msg,*args):
    logging.log(25,msg,*args)
