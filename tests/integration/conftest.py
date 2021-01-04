import shutil
from pathlib import Path
from subprocess import run, CalledProcessError, PIPE
from uuid import uuid4

import pytest
import json

TESTS_PATH = Path(__file__).parents[1].resolve()
REACTIVE_CHARM_PATH = TESTS_PATH / 'charms' / 'reactive-charm'
OPS_CHARM_PATH = TESTS_PATH / 'charms' / 'ops-charm'
INTERFACE_PATH = TESTS_PATH / 'interface' / 'ori-test'
ORI_PATH = TESTS_PATH.parent


def pytest_addoption(parser):
    parser.addoption("--cloud", action="store", default="localhost")
    parser.addoption("--controller", action="store", help="Juju controller")
    parser.addoption("--model", action="store", help="Juju model")
    parser.addoption("--keep", action="store_true",
                     help="Keep controller and / or model")


@pytest.fixture(scope='session')
def check_deps(autouse=True):
    missing = []
    for dep in ('lxd', 'juju', 'charm', 'charmcraft', 'juju-wait'):
        res = run(['which', dep])
        if res.returncode != 0:
            missing.append(dep)
    if missing:
        raise RuntimeError('Missing dependenc{}: {}'.format(
            'y' if len(missing) == 1 else 'ies',
            ', '.join(missing),
        ))


@pytest.fixture(scope='session')
def pydeps(tmp_path_factory):
    pydeps = tmp_path_factory.mktemp('pydeps', False)
    for src in (ORI_PATH, INTERFACE_PATH):
        run(['python', 'setup.py', 'sdist', '-d', str(pydeps)],
            check=True, cwd=str(src))
    return pydeps


@pytest.fixture(scope='session')
def charms_path(tmp_path_factory):
    return tmp_path_factory.mktemp('charms', False)


@pytest.fixture(scope='session')
def builds_path(tmp_path_factory):
    return tmp_path_factory.mktemp('builds', False)


@pytest.fixture(scope='session')
def reactive_charm(pydeps, charms_path, builds_path):
    src = charms_path / 'reactive-charm'
    dst = builds_path / 'reactive-charm'
    wheelhouse_path = src / 'wheelhouse.txt'

    # parameterize wheelhouse.txt to allow installation of built pydeps
    shutil.copytree(str(REACTIVE_CHARM_PATH), str(src))
    wheelhouse_txt = wheelhouse_path.read_text()
    wheelhouse_txt = wheelhouse_txt.format(pydeps=pydeps)
    wheelhouse_path.write_text(wheelhouse_txt)

    run(['charm', 'build', '-d', str(builds_path), str(src)], check=True)
    return dst


@pytest.fixture(scope='session')
def ops_charm(pydeps, charms_path, builds_path):
    src = charms_path / 'ops-charm'
    dst = builds_path / 'ops-charm.charm'
    requirements_path = src / 'requirements.txt'

    # parameterize requirements.txt to allow installation of built pydeps
    shutil.copytree(str(OPS_CHARM_PATH), str(src))
    requirements_txt = requirements_path.read_text()
    requirements_txt = requirements_txt.format(pydeps=pydeps)
    requirements_path.write_text(requirements_txt)

    run(['charmcraft', 'build', '-f', str(src)],
        check=True, cwd=str(builds_path))
    return dst


class Juju:
    def __init__(self, controller=None, model=None):
        self.controller = controller
        self.model = model

    @property
    def full_model(self):
        return self.controller + ':' + self.model

    def controllers(self):
        res = run(['juju', 'controllers', '--format=json'],
                  stdout=PIPE, check=True)
        data = json.loads(res.stdout.decode('utf8'))
        return set((data['controllers'] or {}).keys())

    def models(self):
        res = run(['juju', 'models', '--format=json', '-c', self.controller],
                  stdout=PIPE, check=True)
        models = set()
        for model in json.loads(res.stdout.decode('utf8'))['models']:
            models.add(model['name'])
            models.add(model['short-name'])
        return models

    def bootstrap(self, cloud, name):
        run(['juju', 'bootstrap', cloud, name,
             '--no-switch',
             '--config', 'test-mode=true',
             '--config', 'automatically-retry-hooks=false'], check=True)

    def destroy_controller(self, name):
        run(['juju', 'destroy-controller', '-y', name,
             '--destroy-all-models', '--destroy-storage'], check=True)

    def add_model(self, name):
        run(['juju', 'add-model', '-c', self.controller, name,
             '--no-switch',
             '--config', 'test-mode=true',
             '--config', 'automatically-retry-hooks=false'], check=True)

    def remove_application(self, name, force=False):
        args = [name, '--destroy-storage']
        if force:
            args.append('--force')
        run(['juju', 'remove-application', '-m', self.full_model] + args,
            check=True)

    def destroy_model(self, name, force=False):
        if force:
            # Forcibly remove all applications to prevent errored units from
            # blocking model destruction.
            status = self.status()
            for app in status['applications'].keys():
                self.remove_application(app, force=True)
        run(['juju', 'destroy-model', '-y', self.full_model,
             '--destroy-storage'], check=True)

    def deploy(self, charm, num_units=1):
        if isinstance(charm, Path):
            charm = charm.relative_to(Path.cwd())
        run(['juju', 'deploy', '-m', self.full_model,
             str(charm), '-n', str(num_units)], check=True)

    def add_unit(self, charm):
        run(['juju', 'add-unit', '-m', self.full_model,
             str(charm)], check=True)

    def add_relation(self, a, b):
        run(['juju', 'add-relation', '-m', self.full_model,
             str(a), str(b)], check=True)

    def wait(self):
        try:
            run(['juju', 'wait', '-m', self.full_model, '-wt', str(30 * 60)],
                check=True)
        except CalledProcessError:
            run(['juju', 'status', '-m', self.full_model])
            run(['juju', 'debug-log', '-m', self.full_model,
                 '--replay', '--no-tail',
                 '--include-module', 'unit',
                 '--include-module', 'juju.worker.uniter.operation'])
            raise

    def status(self):
        res = run(['juju', 'status', '--format=json', '-m', self.full_model],
                  stdout=PIPE, check=True)
        return json.loads(res.stdout.decode('utf8'))


@pytest.fixture(scope='session')
def controller(request):
    name = request.config.option.controller or 'test-ori-' + uuid4().hex[:8]
    juju = Juju()
    if name not in juju.controllers():
        juju.bootstrap(request.config.option.cloud, name)
        created = True
    else:
        created = False
    try:
        yield name
    finally:
        if created and not request.config.option.keep:
            juju.destroy_controller(name)


@pytest.fixture
def model(controller, request):
    if request.config.option.model:
        name = request.config.option.model
    else:
        name = request.function.__name__.replace('_', '-')

    juju = Juju(controller, name)
    if name not in juju.models():
        juju.add_model(name)
        created = True
    else:
        created = False
    try:
        yield juju
    finally:
        if created and not request.config.option.keep:
            juju.destroy_model(name, force=True)
