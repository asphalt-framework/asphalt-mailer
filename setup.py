from pathlib import Path

from setuptools import setup

setup(
    name='asphalt-mailer',
    use_scm_version={
        'version_scheme': 'post-release',
        'local_scheme': 'dirty-tag'
    },
    description='Mailer component for the Asphalt framework',
    long_description=Path(__file__).with_name('README.rst').read_text('utf-8'),
    author='Alex Grönholm',
    author_email='alex.gronholm@nextday.fi',
    url='https://github.com/asphalt-framework/asphalt-mailer',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Communications :: Email',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    license='Apache License 2.0',
    zip_safe=False,
    packages=[
        'asphalt.mailer',
        'asphalt.mailer.mailers'
    ],
    setup_requires=[
        'setuptools_scm >= 1.7.0'
    ],
    install_requires=[
        'asphalt ~= 2.0'
    ],
    entry_points={
        'asphalt.components': [
            'mailer = asphalt.mailer.component:MailerComponent'
        ],
        'asphalt.mailer.mailers': [
            'mock = asphalt.mailer.mailers.mock:MockMailer',
            'smtp = asphalt.mailer.mailers.smtp:SMTPMailer',
            'sendmail = asphalt.mailer.mailers.sendmail:SendmailMailer'
        ]
    }
)
