from setuptools import find_packages
from setuptools import setup
from wcheck import __version__

install_requires = ['PyYAML', 'setuptools', 'GitPython', 'rich', 'pendulum', "PyQt5"]

setup(
    name='wcheck',
    version=__version__,
    install_requires=install_requires,
    packages=find_packages(),
    url='https://github.com/PastorD/wcheck',
    author='Daniel Pastor',
    author_email='danpasmor@gmail.com',
    maintainer='Daniel Pastor',
    maintainer_email='danpasmor@gmail.com',
    classifiers=['Intended Audience :: Developers',
                 'License :: MIT Software License',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Version Control',
                 'Topic :: Utilities'],
    description='wcheck compares list of git repositories and checks for differences',
    long_description='wcheck compares list of git repositories and checks for differences',
    entry_points={
        'console_scripts': [
            'wcheck = wcheck.wcheck:main',
        ],
    },
)
