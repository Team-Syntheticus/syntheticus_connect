from setuptools import setup, find_packages
import re

def get_version():
    with open('syntheticus_connect/__init__.py', 'r') as f:
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Unable to find version string.")
setup(
    name='syntheticus_connect',
    version=get_version(), # get the version from the init
    description='A Python client for Syntheticus',
    author='Valerio Mazzone',
    author_email='valerio.mazzone@gmail.com',
    packages=find_packages(),
    install_requires=[
        'requests',
        'pandas',
        'tabulate',
        'ipywidgets',
        'ipython'
        'tornado'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
    ],
)
