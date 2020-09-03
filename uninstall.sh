#!/bin/bash

echo "Removing wellbeing link..."
if rm "$HOME/bin/wellbeing"; then
    echo -e "\033[32mDone.\033[0m"
else
    echo "Something went wrong."
fi

echo ""

echo -e "\e[33mPlease remove the source .../wellbeing_setup.sh"
echo -e "line from your ~/.bashrc or equivalent.\e[0m"
