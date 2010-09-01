#!/usr/bin/env python

METADATA = dict(
	name='python-twblock',
	version='0.1',
	author='Martin Laprise',
	author_email='martin.laprise.1@ulaval.ca',
	description='Twitter stream filter building blocks',
	long_description=open('README.rst').read(),
	url='http://martinlaprise.info/twblock',
	license = 'MIT License',
	keywords='python twitter client block',
)
SETUPTOOLS_METADATA = dict(
	install_requires=['numpy', 'simplegeo', 'PyRSS2Gen'],
	include_package_data=True,
	classifiers=[
		'Development Status :: 4 - Beta',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'Topic :: Software Development :: Libraries :: Python Modules',
		'Topic :: Internet',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
	],
	packages=['twBlock'],
)

if __name__ == '__main__':
	try:
		import setuptools
		METADATA.update(SETUPTOOLS_METADATA)
		setuptools.setup(**METADATA)
	except ImportError:
		import distutils.core
		distutils.core.setup(**METADATA)
