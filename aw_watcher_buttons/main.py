#!/usr/bin/env python3

import sys
import logging
import traceback
from time import sleep
from datetime import datetime, timezone
import tkinter as tk
from tkinter import simpledialog

from aw_core import dirs
from aw_core.models import Event
from aw_client.client import ActivityWatchClient

from .Buttons import Buttons

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
    device_connected = buttons_manager.is_connected()

    root = tk.Tk()
    root.withdraw()

    def prompt_description(button_label):
        root.attributes("-topmost", True)
        root.update()
        description_input = simpledialog.askstring(
            "aw-watcher-buttons",
            f"Whatcha doin with {button_label}?",
            parent=root,
        )
        root.attributes("-topmost", False)
        return description_input

    previous_state = None
    current_title = ""
    current_description = ""
    while True:
        try:
            state = buttons_manager.get_led_state()
            currently_connected = buttons_manager.is_connected()

            if not currently_connected:
                if device_connected:
                    previous_state = None
                    current_title = ""
                    current_description = ""
                device_connected = False
                title = "Buttons disconnected"
                data = {"title": title, "button": "disconnected"}
                print_statusline(title)
                event = Event(timestamp=datetime.now(timezone.utc), data=data)
                aw.heartbeat(bucketname, event, pulsetime=poll_time + 5, queued=True)
                blinked = False
                sleep(poll_time)
                continue

            if not device_connected:
                # Just reconnected, force a new prompt on the next button change.
                previous_state = None
                current_title = ""
                current_description = ""
                device_connected = True

            if 1 <= state <= len(button_names):
                button_name = button_names[state - 1]
                if state != previous_state:
                    description_input = prompt_description(button_name)
                    description = description_input.strip() if description_input else ""
                    current_description = description
                    current_title = (
                        f"{button_name}-{description}" if description else button_name
                    )
                title = current_title or button_name
                data = {"title": title, "button": button_name}
                if current_description:
                    data["description"] = current_description
                print_statusline(title)
                event = Event(timestamp=datetime.now(timezone.utc), data=data)
                aw.heartbeat(bucketname, event, pulsetime=poll_time + 5, queued=True)
                current_time = datetime.now()
                if current_time.minute % 15 == 0 and current_time.second == 0:
                    if not blinked:
                        buttons_manager.blink_led(state, 5, 9)
                    blinked = True
                else:
                    blinked = False
            else:
                title = "No button pressed"
                data = {"title": title, "button": "none"}
                current_title = title
                current_description = ""
                print_statusline(title)
                event = Event(timestamp=datetime.now(timezone.utc), data=data)
                aw.heartbeat(bucketname, event, pulsetime=poll_time + 5, queued=True)

        except Exception as e:
            print("An exception occurred: {}".format(e))
            traceback.print_exc()
            buttons_manager.close()
            sys.exit(1)
        previous_state = state
        sleep(poll_time)


if __name__ == "__main__":
    main()
