#!/usr/bin/env bash
uwsgi --socket 0.0.0.0:5000 --protocol=http -w wsgi --processes 4 --threads 4
