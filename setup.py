from setuptools import setup, find_packages

setup(
	name='dynbsp',
	version_config={
		"template": "{tag}",
		"dev_template": "{tag}.dev{ccount}+git.{sha}",
		"dirty_template": "{tag}.dev{ccount}+git.{sha}.dirty",
		"starting_version": "0.0.1",
		"version_file": "",
		"count_commits_from_version_file": False
	},
	author="James Waters",
	author_email="james@jcwaters.co.uk",
	description="An application to dynamically add, remove and rename desktops from the BSP window manager",
	url="https://github.com/j-waters/dynbsp",
	packages=find_packages(),
	include_package_data=True,
	install_requires=['Click', 'PyYAML'],
	setup_requires=['setuptools-git-versioning'],
	entry_points='''
        [console_scripts]
        dynbsp=dynbsp.__main__:cli
    ''',
	python_requires='>=3.8',
)
