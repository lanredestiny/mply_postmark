#!/bin/bash

if [ $# -eq 0 ]; then
    # No arguments provided, so add --all
    python3 push_email_templates.py --everything
else
    # Pass all provided arguments to the Python script
    python3 push_email_templates.py "$@"
fi
