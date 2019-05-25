import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    raise Exception("Python 3.6 or higher is required. Your version is %s." % sys.version)

__version__ = ""
exec(open('efb_qq_slave/__version__.py').read())

long_description = open('README.rst').read()

setup(
    name='efb-qq-slave',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    version=__version__,
    description='QQ Slave Channel for EH Forwarder Bot, integrated with various QQ Clients.',
    long_description=long_description,
    include_package_data=True,
    author='Milkice',
    author_email='milkice@milkice.me',
    url='https://github.com/milkice233/efb-qq-slave',
    license='GPLv3',
    python_requires='>=3.6',
    keywords=['ehforwarderbot', 'EH Forwarder Bot', 'EH Forwarder Bot Slave Channel',
              'qq', 'chatbot'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Communications :: Chat",
        "Topic :: Utilities"
    ],
    install_requires=[
        "ehforwarderbot",
        "PyYaml",
        'requests', 'python-magic', 'Pillow', 'cqhttp'
    ],
    entry_points={
        'ehforwarderbot.slave': 'milkice.qq = efb_qq_slave:QQMessengerChannel'
    }
)