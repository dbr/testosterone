# (c) 2005 Chad Whitacre <http://www.zetadev.com/>
# This program is beerware. If you like it, buy me a beer someday.
# No warranty is expressed or implied.

prefix=/usr/local

configure: clean
# create the script to be installed
	cp bin/pytest.py pytest
	chmod 555 pytest

# create the man page to be installed
	rm -f pytest.1.gz
	gzip -c -9 man/pytest.1 > pytest.1.gz
	chmod 444 pytest.1.gz

clean:
# delete the script and man page to be installed, as well as the python build
# directory
	rm -rf pytest pytest.1.gz
	rm -rf build

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
