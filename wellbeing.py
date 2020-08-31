#!/usr/bin/env python3
"""Stretch and have some water.

Usage:
    wellbeing -h | --help
    wellbeing [--water=<every> --stretch=<every> --posture=<every>] [(--custom=<every> [--message=<msg>])]

Options:
    -h --help           Show this information.
    --version           Show the version.
    --water=<every>     Remind you to drink water at given interval.
                        If no time unit (h, m, s) is specified,
                        minutes is considered.
    --stretch=<every>   Remind you to stretch at given interval.
    --posture=<every>   Remind you to check your posture at given interval.
    --custom=<every>    Show the custom message at given interval.
    --message=<msg>     The custom message to show.
"""

import subprocess
import internals.schedule as schedule
import time
import re
import os
import os.path
import json
from internals.docopt import docopt


def notify(message: str):
    subprocess.call(["notify-send", message])


def notify_with_title(title: str, message: str):
    subprocess.call(["notify-send", title, message])


TIME_INTERVAL_RE = re.compile(
    '^\s*(\d+(?:\.\d+)?)\s?(h(?:ours)?|m(?:inutes)?|s(?:econds)?)?\s*$', re.IGNORECASE)


def parse_time_interval(raw: str) -> (float, str):
    matches = TIME_INTERVAL_RE.match(raw)
    if matches is None:
        return None
    time = float(matches.group(1))
    unit = matches.group(2)
    if unit is None:
        unit = 'minutes'
    elif unit.startswith('s'):
        unit = 'seconds'
    elif unit.startswith('m'):
        unit = 'minutes'
    elif unit.startswith('h'):
        unit = 'hours'
    return (time, unit)


def unwrap_time_interval(raw: str) -> (float, str):
    time_unit = parse_time_interval(raw)
    if time_unit is None:
        print(f"could not read {raw} as a time.")
        print("expected, for example, '15m', '5 minutes', '2.5 hours'.")
        exit(1)
    return time_unit


def parse_and_set_job(argument, job):
    if argument:
        time, unit = unwrap_time_interval(argument)
        if unit == 'seconds':
            schedule.every(time).seconds.do(job)
        elif unit == 'minutes':
            schedule.every(time).minutes.do(job)
        elif unit == 'hours':
            schedule.every(time).hours.do(job)


def parse_json_message(messages_json: dict, variant: str) -> (str, str):
    if variant not in messages_json["messages"]:
        print(f"No message specified for {variant} in given JSON file.")
        print("Aborting")
        exit(1)

    if "title" not in messages_json["messages"][variant]:
        print(f"Need at least a title for the {variant} message.")
        print("Aborting")
        exit(1)

    return (
        messages_json["messages"][variant]["title"],
        messages_json["messages"][variant].get("description", ""))


def parse_json_message_optional(messages_json: dict, variant: str) -> (str, str):
    if variant not in messages_json["messages"]:
        return None

    if "title" not in messages_json["messages"][variant]:
        return None

    return (
        messages_json["messages"][variant]["title"],
        messages_json["messages"][variant].get("description", ""))


if __name__ == '__main__':
    EXPECTED_JSON_VERSION = 1.0
    arguments = docopt(__doc__, version="Wellbeing 1.0")

    if all(not x for x in arguments.values()):
        print(__doc__)
        exit(0)

    messages_file = os.environ.get("WELLBEING_MSGS",
                                   os.path.join(os.path.basename(__file__), "messages.json"))
    if not os.path.exists(messages_file):
        print("Could not find the messages JSON file.")
        print("Please make sure that WELLBEING_MSGS is set in your environment variables,")
        print("and that it is pointing to a valid file.")
        exit(1)

    with open(messages_file) as messages_io:
        messages_json = json.load(messages_io)

        if "version" not in messages_json:
            print("Warning: No version specification. " +
                  f"If the program crashes, make sure that {messages_file} is correctly formatted.")
        else:
            if messages_json["version"] != EXPECTED_JSON_VERSION:
                print(
                    f"Warning: Unexpected version attribute value (expected {EXPECTED_JSON_VERSION}).")
                print("Will continue anyway.")

        if "messages" not in messages_json:
            print("No 'messages' attribute in given JSON file.")
            print("Aborting.")
            exit(1)

        water_msg = parse_json_message(messages_json, "water")
        stretch_msg = parse_json_message(messages_json, "stretch")
        posture_msg = parse_json_message(messages_json, "posture")
        custom_msg = parse_json_message_optional(messages_json, "custom")

    if arguments['--message']:
        custom_msg = (arguments['--message'], "")
    if arguments['--custom'] and not custom_msg:
        print("No message defined for custom timer!")
        print("Aborting.")
        exit(1)

    def water_job():
        if all(water_msg):
            notify_with_title(*water_msg)
        else:
            notify(water_msg[0])

    def stretch_job():
        if all(stretch_msg):
            notify_with_title(*stretch_msg)
        else:
            notify(stretch_msg[0])

    def posture_job():
        if all(posture_msg):
            notify_with_title(*posture_msg)
        else:
            notify(posture_msg[0])

    def custom_job():
        if all(custom_msg):
            notify_with_title(*custom_msg)
        else:
            notify(custom_msg[0])

    parse_and_set_job(arguments['--water'], water_job)
    parse_and_set_job(arguments['--stretch'], stretch_job)
    parse_and_set_job(arguments['--posture'], posture_job)
    parse_and_set_job(arguments['--custom'], custom_job)

    print("I'm running! Feel free to leave me in the background.")
    while True:
        schedule.run_pending()
        time.sleep(1)