from setuptools import setup

setup(
    name='nexus-cli',
    version='0.1',
    py_modules=['cli'],
    install_requires=[
        'click',
        'blessings',
        'python-keycloak',
        'requests==2.18.4',
        'prettytable',
        'PyJWT',
        'pygments'
    ],
    entry_points='''
        [console_scripts]
        nexus=cli:entry_point
    ''',
)
