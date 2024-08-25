#!/usr/bin/env python3

import sys
import logging
import traceback
from time import sleep
from datetime import datetime, timezone

from aw_core import dirs
from aw_core.models import Event
from aw_client.client import ActivityWatchClient

from Buttons import Buttons

watcher_name = "aw-watcher-buttons"

logger = logging.getLogger(watcher_name)
DEFAULT_CONFIG = f"""
[{watcher_name}]
poll_time = 0.1
port = ""
button_names = ["green", "red", "white", "blue", "yellow"]
"""


def load_config():
    from aw_core.config import load_config_toml as _load_config

    return _load_config(watcher_name, DEFAULT_CONFIG)


def print_statusline(msg):
    last_msg_length = (
        len(print_statusline.last_msg) if hasattr(print_statusline, "last_msg") else 0
    )
    print(" " * last_msg_length, end="\r")
    print(msg, end="\r")
    print_statusline.last_msg = msg


def main():
    logging.basicConfig(level=logging.INFO)

    config_dir = dirs.get_config_dir(watcher_name)

    config = load_config()

    port = config[watcher_name].get("port")
    port = None if port == "" else port
    poll_time = float(config[watcher_name].get("poll_time"))
    button_names = config[watcher_name].get("button_names")
    if port is None or button_names is None:
        logger.error(
            "Port and button names must be specified in the config file. You can find it here: {}".format(
                config_dir
            )
        )
        sys.exit(1)

    aw = ActivityWatchClient(watcher_name, testing=False)
    bucketname = "{}_{}".format(aw.client_name, aw.client_hostname)
    if aw.get_buckets().get(bucketname) == None:
        aw.create_bucket(bucketname, event_type="Button", queued=True)
    aw.connect()
    buttons_manager = Buttons(port)
    blinked = False
    while True:
        try:
            state = buttons_manager.get_led_state()
            if state != -1:
                button_name = button_names[state - 1]
                title = f"{button_name}"
                data = {"title": title, "button": button_name}
                print_statusline(title)
                event = Event(timestamp=datetime.now(timezone.utc), data=data)
                aw.heartbeat(bucketname, event, pulsetime=poll_time + 1, queued=True)
            else:
                title = "No button pressed"
                data = {"title": title, "button": "none"}
                print_statusline(title)
                event = Event(timestamp=datetime.now(timezone.utc), data=data)
                aw.heartbeat(bucketname, event, pulsetime=poll_time + 1, queued=True)
            current_time = datetime.now()
            if current_time.minute % 15 == 0 and current_time.second == 0:
                if not blinked:
                    buttons_manager.blink_led(state, 3, 4)
                    blinked = True
            else:
                blinked = False

        except Exception as e:
            print("An exception occurred: {}".format(e))
            traceback.print_exc()
            buttons_manager.close()
            sys.exit(1)
        sleep(poll_time)


if __name__ == "__main__":
    main()
