#!/usr/bin/env bash

version_type=$1

rm -rf build dist goodreads_user_scraper.egg-info
python3 setup.py sdist bdist_wheel
twine check dist/*
bumpversion $version_type
twine upload dist/*
