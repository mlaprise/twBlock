twBlock - Twitter stream filter building blocks
===================================================


Requirements
---------------------------------------------------
	* PyRSS2Gen
	* python-simplegeo
	* python-twython


Installation
---------------------------------------------------

from the source ::

	git clone git://github.com:mlaprise/twBlock.git
	cd twBlock
	sudo python setup.py install


Example
---------------------------------------------------

Simple Hello world example ::

from twBlock import *

mySource = twSource('user', 'password')

mySource.terminal()
