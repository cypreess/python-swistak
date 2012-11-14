from setuptools import find_packages, setup

setup(
    name='python-swistak',
    description='Python client for swistak.pl WebAPI',
    long_description='',
    version='0.1dev',
    packages=['swistak',],
    license='MIT',
    author='Krzysztof Dorosz',
    author_email='cypreess@gmail.com',
    install_requires=['suds'],
)