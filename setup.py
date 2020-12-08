from setuptools import setup


SETUP = {
    'name': "ops_reactive_interface",
    'version': '1.0.0',
    'author': "Cory Johns",
    'author_email': "cory.johns@canonical.com",
    'url': "https://github.com/juju-solutions/ops-reactive-interface",
    'py_modules': ['ops_reactive_interface'],
    'install_requires': [
        'ops>=1.0.0',
    ],
    'entry_points': {
        'charms.reactive.relation_factory':
            'interface_api = ops_reactive_interface:InterfaceAPIFactory',
    },
    'license': "Apache License 2.0",
    'long_description_content_type': 'text/markdown',
    'long_description': open('README.md').read(),
    'description': 'Helper for interface APIs written for '
                   'the charm operator framework, which can '
                   'register them with charms.reactive to '
                   'function similarly to Endpoints.',
}


if __name__ == '__main__':
    setup(**SETUP)
