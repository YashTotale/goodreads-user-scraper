#!/usr/bin/env bash

version_type=$1

# Source environment variables
if [ -f .env ]
then
  export $(cat .env | sed 's/#.*//g' | xargs)
fi

rm -rf build dist goodreads_user_scraper.egg-info
bump-my-version bump $version_type
python setup.py sdist bdist_wheel
twine check dist/*
twine upload dist/*
git push
git push --follow-tags
