from setuptools import setup


SETUP = {
    'name': "oi-test",
    'version': '1.0.0',
    'author': "Cory Johns",
    'author_email': "johnsca@gmail.com",
    'url': "https://github.com/juju-solutions/ops-reactive-interface",
    'py_modules': ['ori_test'],
    'install_requires': [
        'ops>=1.0.0',
        'ops_reactive_interface',
    ],
    'entry_points': {
        'ops_reactive_interface.provides': 'ori-test = ori_test:ORITest',
        'ops_reactive_interface.requires': 'ori-test = ori_test:ORITest',
        'ops_reactive_interface.peers': 'ori-test = ori_test:ORITest',
    },
    'license': "Apache License 2.0",
    'description': 'Test interface for ops_reactive_interface',
}


if __name__ == '__main__':
    setup(**SETUP)
