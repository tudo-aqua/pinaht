#!/bin/bash

if [ ! -d "source/_static" ]
then
	mkdir source/_static
fi

if [ ! -d "source/_templates" ]
then
	mkdir source/_templates
fi

# update project structure
sphinx-apidoc -e -f -o source/generated_rst ../pinaht
rm source/generated_rst/modules.rst

# build docs
make html

# open standard browser
if [ "${1}" = "show" ]
then
	xdg-open build/html/index.html
fi
