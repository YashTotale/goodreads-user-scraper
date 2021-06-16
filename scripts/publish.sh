#!/usr/bin/env bash

version_type=$1

# Source environment variables
if [ ! -f .env ]
then
  export $(cat .env | xargs)
fi

rm -rf build dist goodreads_user_scraper.egg-info
python3 setup.py sdist bdist_wheel
twine check dist/*
bumpversion $version_type
git push
git push --follow-tags
twine upload dist/*
