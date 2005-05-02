# (c) 2005 Chad Whitacre <http://www.zetadev.com/>
# This program is beerware. If you like it, buy me a beer someday.
# No warranty is expressed or implied.

prefix=/usr/local

# release parameters
version=0.3
man_prefix = /usr/local/www/www.zetadev.com/software/pytest/trunk/man

configure: clean
# create the script to be installed
	cp bin/pytest.py pytest
	chmod 555 pytest

# create the man page to be installed
	rm -f pytest.1.gz
	gzip -c -9 man/man1/pytest.1 > pytest.1.gz
	chmod 444 pytest.1.gz

clean:
# remove all of the cruft that gets auto-generated on doc/install/release
	rm -rf pytest pytest.1.gz
	rm -rf build
	rm -rf doc/api
	rm -rf doc/python.1.html
	rm -rf dist
	rm -rf MANIFEST

install: configure
# after deleting and recreating the script and man page, install them
	install -C -o root -g wheel -m 555 pytest ${prefix}/bin
	install -C -o root -g wheel -m 444 pytest.1.gz ${prefix}/man/man1
# also install the Python package
	python setup.py install

uninstall:
# delete the script and man page from their installed locations
	rm -f ${prefix}/bin/pytest
	rm -f ${prefix}/man/man1/pytest.1.gz
# note that the result of setup.py is not undone


release:clean
# after installing the program, do some things for a release
# build a source distribution (setup.py sdist doesn't allow for Makefile, etc.)
	mkdir -p dist/pytest-${version}
	mkdir -p dist/pytest-${version}/doc
	cp -r bin dist/pytest-${version}/
	cp -r man dist/pytest-${version}/
	cp -r site-packages dist/pytest-${version}/
	cp Makefile setup.py

	tar zcf dist/pytest-0.3.tar.gz
	epydoc -o doc/api site-packages/PyTest site-packages/ASTutils
	man -M ${man_prefix} pytest | rman -f HTML > doc/pytest.1.html
