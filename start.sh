#!/bin/bash
playwright install
python login_once.py
python fb_scraper.py
