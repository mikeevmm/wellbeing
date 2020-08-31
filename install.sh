#!/bin/bash

if ! notify-send -v >/dev/null 2>&1; then
	echo -e "\033[91mnotify-send is required, but was not found.\033[0m"
	echo -e "\033[91mAborting.\033[0m"
	exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo -e "This script will add a symlink from"
echo -e "$HOME/bin/"
echo -e "to"
echo -e "$DIR/wellbeing.py"
echo -e "so that you can call wellbeing from any directory."
read -p $'\033[33mIs this ok [N/y]?\033[0m ' -r
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1
fi

if [ ! -d $HOME/bin ]; then
    echo -e "$HOME/bin does not exist, creating that directory."
    read -p "Is this ok [N/y]? " -n 1 -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]
    then
        [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1
    fi
    mkdir $HOME/bin
    export PATH="$HOME/bin:$PATH"
    echo -e "\033[32mCreated $HOME/bin\033[0m"
fi

if ln -s "$DIR/wellbeing.py" "$HOME/bin/wellbeing"
then
	echo -e "\033[32mDone.\033[0m"
else
    echo -e "\033[91mSomething went wrong.\033[0m"
fi

echo ""

echo -e "\e[33mPlease add the following line to your ~/.bashrc or equivalent:\e[0m"
echo "export WELLBEING_MSGS=$DIR/messages.json"

echo ""

echo -e "Call \`wellbeing --help\` for more info."
