#!/usr/bin/env bash

version_type=$1

bump-my-version bump "$version_type"
git push
git push --follow-tags
