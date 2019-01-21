from setuptools import setup

setup(
    name='nexus-cli',
    version='0.2',
    py_modules=['cli'],
    packages=["nexuscli"],
    install_requires=[
        'click',
        'blessings',
        'prettytable',
        'PyJWT',
        'pygments',
        'pytest',
		'nexus-sdk==0.1.0' 
	],
    entry_points='''
        [console_scripts]
        nexus=nexuscli.cli:cli
    ''',
)
