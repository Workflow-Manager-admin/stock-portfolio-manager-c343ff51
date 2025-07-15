#!/bin/bash
cd /home/kavia/workspace/code-generation/stock-portfolio-manager-c343ff51/backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

