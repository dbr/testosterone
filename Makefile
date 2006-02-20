# (c) 2005 Chad Whitacre <http://www.zetadev.com/>
# This program is beerware. If you like it, buy me a beer someday.
# No warranty is expressed or implied.

prefix=/usr/local


configure:
# create the script to be installed
	cp bin/testosterone testosterone
	chmod 555 testosterone


# create the man page to be installed
	rm -f testosterone.1.gz
	gzip -c -9 doc/testosterone.1 > testosterone.1.gz
	chmod 444 testosterone.1.gz


clean:
# remove all of the cruft that gets auto-generated on doc/install/release
	rm -rf testosterone testosterone.1.gz
	rm -rf build
	rm -rf dist
	find . -name \*.pyc | xargs rm


install: configure
# after deleting and recreating the script and man page, install them
	install -C -o root -g wheel -m 555 testosterone ${prefix}/bin
	install -C -o root -g wheel -m 444 testosterone.1.gz ${prefix}/man/man1
# also install the Python package
	python setup.py install


uninstall:
# delete the script and man page from their installed locations
	rm -f ${prefix}/bin/testosterone
	rm -f ${prefix}/man/man1/testosterone.1.gz
# note that the result of setup.py is not undone




##
# targets for generating docs and doing a release
##

# release parameters -- not meaningful for local use
version=trunk
man_prefix = /usr/local/www/www.zetadev.com/software/pytest/${version}/man


docs:
# auto-generate some docs
	epydoc -o doc/api site-packages/PyTest site-packages/ASTutils
	man -M ${man_prefix} pytest | rman -f HTML > doc/pytest.1.html


release:clean docs
# do a release; not using setup.py because afaict sdist doesn't allow for
# Makefile, etc.

# build a source distribution
	mkdir -p pytest-${version}/doc
	cp -r doc/tutorial.pyt pytest-${version}/doc
	cp -r doc/api pytest-${version}/doc/api
	cp -r bin pytest-${version}/
	cp -r man pytest-${version}/
	cp -r site-packages pytest-${version}/
	cp README setup.py pytest-${version}/
	cp Makefile-release pytest-${version}/Makefile

# tar it up
	mkdir dist
	tar zcf dist/pytest-${version}.tar.gz pytest-${version}
	tar cf dist/pytest-${version}.tar pytest-${version}
	bzip2 dist/pytest-${version}.tar

# and clean up
	rm -rf pytest-${version}
