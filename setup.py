from setuptools import setup, find_packages

setup(
	name='dynbsp',
	version='0.1',
	packages=find_packages(),
	include_package_data=True,
	install_requires=['Click', 'PyYAML'],
	entry_points='''
        [console_scripts]
        dynbsp=dynbsp.__main__:cli
    ''',
)
