#!/usr/bin/env python3
"""[__doc__ is generated in generate_doc().]"""

import subprocess
import internals.schedule as schedule
import time
import re
import os
import os.path
import json
import hashlib
from internals.docopt import docopt
from itertools import chain


TIME_INTERVAL_RE = re.compile(
    r'^\s*(\d+(?:\.\d+)?)\s?(h(?:ours?)?|m(?:inutes?)?|s(?:econds?)?)?\s*$', re.IGNORECASE)
CLOCK_TIME_RE = re.compile(
        r'^\s*\d{1,2}\:\d{1,2}\s*$', re.IGNORECASE)

EXPECTED_JSON_VERSION = 2.0
JSON_ENVAR = "WELLBEING_JSON"
HASH_ENVAR = "WELLBEING_HASH"
DOC_ENVAR  = "WELLBEING_DOC"
DEFAULT_JSON_ENVAR = os.path.join(os.path.basename(__file__), "messages.json")
DEFAULT_HASH_ENVAR = os.path.join(os.path.basename(__file__), "internals", "messages.json.hash")
DEFAULT_DOC_ENVAR = os.path.join(os.path.basename(__file__), "internals", "messages.json.doc")
DOC_TEMPLATE = lambda usage, options: f"""Stretch and have some water.

Usage:
    {usage}
    wellbeing --help | -h

Options:
{options}
"""

NO_JSON = f"""Couldn't find a messages.json file.
Please ensure an environment variable '{JSON_ENVAR}' exists, and points to a valid messages.json file, or that
'{DEFAULT_JSON_ENVAR}'
exists."""
NO_JSON_HASH = f"""Couldn't find a messages.json.hash file.
Please ensure an environment variable '{HASH_ENVAR}' exists, and points to a writeable messages.json.hash file, or that
'{DEFAULT_HASH_ENVAR}'
exists."""
NO_DOC = f"""Couldn't find a messages.json.doc file.
Please ensure an environment variable '{DOC_ENVAR}' exists, and points to a writeable messages.json.doc file, or that
'{DEFAULT_DOC_ENVAR}'
exists."""
NO_VERSION = """Warning: Couldn't find a 'version' property of the messages.json file.
Your file may be misforatted, and a crash may result from this."""
BAD_VERSION = lambda expected, given, location: f"""Error: Bad messages.json version.
Expected {expected}, got {given}.
Please update your messages.json(*) to match the current version(**).
(*): Found at \"{location}\"
(**): See [https://github.com/mikeevmm/wellbeing/blob/master/messages.json]
Aborting."""
NO_COMMANDS = lambda location: """Error: No 'commands' field in messages.json.
Please ensure your messages.json(*) is correctly formatted.
See [https://github.com/mikeevmm/wellbeing/blob/master/messages.json] for an example messages.json.
(*): Found at \"{location}\" """
BAD_COMMANDS = """Error: 'commands' field exists in messages.json, but is not of the correct type.
See [https://github.com/mikeevmm/wellbeing/blob/master/messages.json] for an example messages.json.
Aborting."""
NO_EVERY = """Error: 'commands' field in messages.json does not have an 'every' field. This field is required, even if empty (\"every\": {}).
Aborting."""
BAD_EVERY = """Error: 'every' field exists within 'commands' field, but is not of the correct type.
See [https://github.com/mikeevmm/wellbeing/blob/master/messages.json] for an example messages.json.
Aborting."""
NO_AT = """Error: 'commands' field in messages.json does not have an 'at' field. This field is required, even if empty (\"at\": {}).
Aborting."""
BAD_AT = """Error: 'at' field exists within 'commands' field, but is not of the correct type.
See [https://github.com/mikeevmm/wellbeing/blob/master/messages.json] for an example messages.json.
Aborting."""
BAD_COMMAND = lambda command, within, missing: f"""Error: Command '{command}' (defined within '{within}') does not define {missing}, which is required.
See [https://github.com/mikeevmm/wellbeing/blob/master/messages.json] for an example messages.json.
Aborting."""
BAD_NOTIFICATION = lambda command, within: f"""Error: Field 'notification' of '{command} (defined within '{within}') exists, but is not of the correct type.
Expected a string.
See [https://github.com/mikeevmm/wellbeing/blob/master/messages.json] for an example messages.json.
Aborting."""
BAD_DESCRIPTION = lambda command, within: f"""Error: Field 'description' of '{command}' (defined within '{within}') exists, but is not of the correct type.
Expected a dictionary with 'title' and optional 'description' fields. 
See [https://github.com/mikeevmm/wellbeing/blob/master/messages.json] for an example messages.json.
Aborting."""
NO_TITLE = lambda command, within: f"""Error: No title field in notification description of '{command}'.
(defined within '{within}')
'description' field is optional, but 'title' field is required.
Aborting."""
RUN_BAD_EVERY = lambda command, bad_every: f"""Cannot read {bad_every} as a time interval.
Expected format:
    XXXh or XXX hour or XXX hours
    XXXm or XXX minute or XXX minutes
    XXXs or XXX second or XXX seconds
Got:
    {bad_every}"""
RUN_BAD_CLOCK = lambda command, bad_clock: f"""Cannot read {bad_clock} as a clock time.
Expected format:
    XX:XX
Got:
    {bad_clock}"""
RUNNING = """I'm running! Feel free to leave me in the background."""


def get_json() -> (bool, str, object):
    hash_loc = os.environ.get(HASH_ENVAR, DEFAULT_HASH_ENVAR)
    if not os.path.exists(hash_loc):
        print(NO_JSON_HASH)
        exit(1)

    json_loc = os.environ.get(JSON_ENVAR, DEFAULT_JSON_ENVAR)
    if not os.path.exists(json_loc):
        print(NO_JSON)
        exit(1)

    with open(json_loc) as json_io:
        json_obj = json.load(json_io)

    with open(hash_loc, 'r+b') as hash_io:
        hash_value = hash_io.read()
        hasher = hashlib.sha256()
        hasher.update(json.dumps(json_obj).encode('utf-8'))
        # Include the python source in the hash, so that changes
        # to the program also force the json/doc to be re-parsed.
        with open(os.path.abspath(__file__), 'r+b') as self_io:
            hasher.update(self_io.read())
        new_hash = hasher.digest()
    if new_hash == hash_value:
        return False, json_loc, json_obj

    if "version" not in json_obj:
        print(NO_VERSION)
    else:
        if json_obj["version"] != EXPECTED_JSON_VERSION:
            print(BAD_VERSION(
                EXPECTED_JSON_VERSION,
                json_obj["version"],
                json_loc))
            exit(1)
    if "commands" not in json_obj:
        print(NO_COMMANDS)
        exit(1)
    if type(json_obj["commands"]) is not dict:
        print(BAD_COMMANDS)
        exit(1)
    if "every" not in json_obj["commands"]:
        print(NO_EVERY)
        exit(1)
    if type(json_obj["commands"]["every"]) is not dict:
        print(BAD_EVERY)
        exit(1)
    if "at" not in json_obj["commands"]:
        print(NO_AT)
        exit(1)
    if type(json_obj["commands"]["at"]) is not dict:
        print(BAD_AT)
        exit(1)
    for command, parent in chain(
            ((x, "every") for x in json_obj["commands"]["every"]),
            ((x, "at") for x in json_obj["commands"]["at"])):
        if "notification" not in json_obj["commands"][parent][command]:
            print(BAD_COMMAND(command, "notification", parent))
            exit(1)
        if "description" not in json_obj["commands"][parent][command]:
            print(BAD_COMMAND(command, "description", parent))
        if type(json_obj["commands"][parent][command]["notification"]) is not dict:
            print(BAD_NOTIFICATION(command, parent))
            exit(1)
        if type(json_obj["commands"][parent][command]["description"]) is not str:
            print(BAD_DESCRIPTION(command, parent))
            exit(1)
        if "title" not in json_obj["commands"][parent][command]["notification"]:
            print(NO_TITLE(command, parent))
            exit(1)

    with open(hash_loc, 'w+b') as hash_io:
        hash_io.write(new_hash)

    return True, json_loc, json_obj


def generate_doc(file_updated, json_obj):
    doc_loc = os.environ.get(DOC_ENVAR, DEFAULT_DOC_ENVAR)
    if not os.path.exists(doc_loc):
        print(NO_DOC)
        exit(1)
    if not file_updated:
        with open(doc_loc) as doc_io:
            return doc_io.read()
    commands = []
    for parent, command in chain(
        (('every', x) for x in json_obj['commands']['every']),
        (('at', x) for x in json_obj['commands']['at'])):
       command = f'[--{command}=<{parent}>]'
       commands.append(command)
    formatted_command = ' '.join(['wellbeing', *commands])

    options = []
    for parent, command in chain(
        (('every', x) for x in json_obj['commands']['every']),
        (('at', x) for x in json_obj['commands']['at'])):
        description = json_obj['commands'][parent][command]['description']
        option = [f'--{command}=<{parent}>', description]
        options.append(option)
    options.append(["--help -h", "Show this screen."])

    formatted_options = []
    right_align = max(len(x[0]) for x in options) + 2
    for left, right in options:
        formatted_option = ' '*4
        formatted_option += left
        formatted_option += ' '*(right_align - len(left))
        formatted_option += right
        formatted_options.append(formatted_option)
    formatted_options = '\n'.join(formatted_options)

    doc = DOC_TEMPLATE(formatted_command, formatted_options)
    with open(doc_loc, 'w') as doc_io:
        doc_io.write(doc)
    return doc


def notify(message: str):
    subprocess.call(["notify-send", message])


def notify_with_title(title: str, message: str):
    subprocess.call(["notify-send", title, message])


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


if __name__ == '__main__':
    changed, json_loc, json_obj = get_json()
    __doc__ = generate_doc(changed, json_obj)
    arguments = docopt(__doc__, version="Wellbeing 2.0")
    if not any(x for x in arguments.values()):
        print(__doc__)
        exit(0)

    for option in json_obj['commands']['every']:
        command = f'--{option}'
        if arguments[command]:
            time_unit = parse_time_interval(arguments[command])
            if time_unit is None:
                print(RUN_BAD_EVERY(option, arguments[command]))
                exit(1)
            run_time, unit = time_unit
            
            title = json_obj['commands']['every'][option]['notification']['title']
            description = json_obj['commands']['every'][option]['notification'].get('description', '')
            if description:
                job = lambda: notify_with_title(title, description)
            else:
                job = lambda: notify(title)
            
            if unit == 'seconds':
                schedule.every(run_time).seconds.do(job)
            elif unit == 'minutes':
                schedule.every(run_time).minutes.do(job)
            elif unit == 'hours':
                schedule.every(run_time).hour.do(job)
            else:
                raise ValueError("Unexpected match for time unit")
    
    for option in json_obj['commands']['at']:
        command = f'--{option}'
        if arguments[command]:
            if not CLOCK_TIME_RE.match(arguments[command]):
                print(RUN_BAD_CLOCK(option, arguments[command]))
                exit(1)

            title = json_obj['commands']['at'][option]['notification']['title']
            description = json_obj['commands']['at'][option]['notification'].get('description', '')
            if description:
                job = lambda: notify_with_title(title, description)
            else:
                job = lambda: notify(title)
            schedule.every().day.at(arguments[command]).do(job)

    print(RUNNING)
    while True:
        schedule.run_pending()
        time.sleep(1)
