#!/usr/bin/env bash

rm -rf goodreads-data
python3 -m scraper --user_id 54739262 --output_dir goodreads-data
