from setuptools import setup

setup(
    name='nexus-cli',
    version='0.2.0',
    description='A Command Line Interface (CLI) for Blue Brain Nexus.',
    keywords='nexus cli',
    url="https://github.com/BlueBrain/nexus-cli",
    author="Samuel Kerrien, Mohameth Francois Sy",
    author_email="samuel.kerrien@epfl.ch, mohameth.sy@epfl.ch",
    license="Apache License, Version 2.0",
    python_requires=">=3.5",
    py_modules=['cli'],
    packages=["nexuscli"],
    install_requires=[
        'click',
        'blessings',
        'prettytable',
        'PyJWT',
        'pygments',
        'pandas',
        'pytest',
        'nexus-sdk'
    ],
    entry_points='''
        [console_scripts]
        nexus=nexuscli.cli:cli
    ''',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "Topic :: Database",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5'",
        "Programming Language :: Python :: 3.6'",
        "Programming Language :: Python :: 3.7'",
        "Programming Language :: Python :: 3.8'",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Natural Language :: English",
    ]
)
