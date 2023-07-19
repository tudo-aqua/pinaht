#!/bin/bash

askback=false

# get all staged python files
sfiles=$(git diff --name-only --staged | grep --color=never '\.py$' | tr '\n' ' ')

# test if files would be reformatted
black_test=$(black -l 118 -t py37 --check --diff $sfiles 2>&1)

if [ $? -eq 1 ]
then
	echo "Black would reformat some files:"
	echo "#------------------------------------------------------------------------------#"
	echo "#------------------------------------BLACK-------------------------------------#"
	echo "#------------------------------------------------------------------------------#"
	echo "${black_test}"
	if [ "$askback" = true ]
	then
		read -p "Would you like to reformat them right now? [y|n] " -n 1 -r < /dev/tty
		if echo $REPLY | grep -E '^[Yy]$' > /dev/null
		then
			echo ""
			black -l 118 -t py37 $sfiles 2>&1

			black -l 118 -t py37 --check --diff $sfiles > /dev/null 2>&1

			if [ $? -eq 1 ]
			then
				echo "Looks like black could not fix all errors by himself :/"
				exit 1
			fi

			exit 1
		else
			echo ""
			exit 1
		fi
	else
		exit 1
	fi
fi

# test if files are PEP-8 compatible
flake_test=$(flake8 --show-source --statistics --max-line-length=118 $sfiles)
if [ $? -eq 1 ]
then
	echo "Your code is not PEP-8 compatible!"
	echo "#------------------------------------------------------------------------------#"
	echo "#------------------------------------FLAKE-------------------------------------#"
	echo "#------------------------------------------------------------------------------#"
	echo "${flake_test}"
	exit 1
fi

exit 0
