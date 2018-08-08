from setuptools import setup

setup(
    name='nexus-cli',
    version='0.1',
    py_modules=['cli'],
    install_requires=[
        'Click',
        'blessings',
        'python-keycloak',
        'requests',
        'prettytable',
        'jwt'
    ],
    entry_points='''
        [console_scripts]
        nexus-cli=cli:entry_point
    ''',
)