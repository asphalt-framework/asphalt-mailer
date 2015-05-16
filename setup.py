import os.path

from setuptools import setup

here = os.path.dirname(__file__)
readme_path = os.path.join(here, 'README.rst')
readme = open(readme_path).read()

setup(
    name='asphalt-mailer',
    version='1.0',
    description='Email extension for the Asphalt framework',
    long_description=readme,
    author='Alex Grönholm',
    author_email='alex.gronholm+pypi@nextday.fi',
    url='http://pypi.python.org/pypi/asphalt-mailer/',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ],
    license='MIT',
    zip_safe=True,
    packages=[
        'asphalt.extension.mailer'
    ],
    install_requires=[
        'asphalt >= 1.0.0',
        'marrow.mailer >= 4.0.0'
    ],
    entry_points={
        'asphalt.extensions': [
            'mailer = asphalt.extension.mailer:MailerExtension'
        ]
    }
)
