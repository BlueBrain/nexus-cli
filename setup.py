from setuptools import setup

setup(
    name='nexus-cli',
    version='0.1',
    py_modules=['cli'],
    install_requires=[
        'click',
        'blessings',
        'requests',
        'prettytable',
        'PyJWT',
        'pygments',
        'pytest',
		'nexus-sdk==0.1.0' 
	],
    entry_points='''
        [console_scripts]
        nexus=cli:entry_point
    ''',
)
