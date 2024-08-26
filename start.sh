#!/usr/bin/env bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 5000 --workers 1
