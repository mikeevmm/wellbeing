# Wellbeing

No-nonsense command to remind you to take care of yourself.

This terminal utility allows you to set up a timer to remind
you to drink water, stretch, check your posture, or other activities.

``` bash
wellbeing --water="1 hour" --posture=5m --stretch=30m
```

The command is driven by the `messages.json` file, so you can add
commands easily. See [Adding New Commands](#adding-new-commands) for
details.

## Quick Start

``` bash
git clone https://github.com/mikeevmm/wellbeing
cd wellbeing
bash install.sh
wellbeing --help
```

## Adding New Commands

Every command is defined by an entry in `messages.json` , under `commands` .
Commands are split into two types: `every` , which are things to remind you of
at fixed intervals, and `at` , which are things to remind you of at some clock time.
Command entries are defined as follows:

``` json
"<command name>": {
    "notification": {
        "title": "<what to show at the top of the notification>",
        "description": "<what to show in the text of the notification>"
    },
    "description": "<the description of the command in the help screen>"
}
```

where `<elements between brackets>` are to be replaced by you.
For example, an entry in `every` of the form

``` json
"water": {
    "notification": {
        "title": "Water",
        "description": "Remember to drink some water!"
    },
    "description": "Reminder to drink water at given interval."
},
```

allows you to call `wellbeing --water=10m` to get a reminder to drink water every 10 minutes.

The notification description field is also optional (in which case the notification only has
a title):

``` json
"posture": {
    "notification": {
        "title": "Posture Check"
    },
    "description": "Reminder to stretch at given interval."
}
```

## Upgrading From 1.0

It's recommended, if upgrading from an existing (1.0) `wellbeing` installation, 
to follow the following steps:

``` shell
bash uninstall.sh
git pull
bash install.sh
```

and follow the on-screen instructions.

## License

This tool is licensed under an MIT license.
See LICENSE for details.

## Support

💕 If you liked wellbeing, consider [buying me a coffee](https://www.paypal.me/miguelmurca/2.50).
