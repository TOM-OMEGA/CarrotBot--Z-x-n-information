#!/bin/bash
export PLAYWRIGHT_BROWSERS_PATH=0
playwright install
python login_once.py
python fb_scraper.py
