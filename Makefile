
.PHONY: all home-install clean

all: build/update

build/update: src/update.py
	mkdir --parents -- build
	printf '%s\n\n' '#!/bin/env python3.5' > $@
	cat $< >> $@
	chmod a+x $@

home-install: build/update
	cp $< ~/bin/update

clean:
	rm --recursive --force -- build
