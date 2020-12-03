import shutil
import uuid
from pathlib import Path
from subprocess import run, CalledProcessError

import pytest
import json

TESTS_PATH = Path(__file__).parents[1].resolve()
REACTIVE_CHARM_PATH = TESTS_PATH / 'charms' / 'reactive-charm'
OPS_CHARM_PATH = TESTS_PATH / 'charms' / 'ops-charm'
INTERFACE_PATH = TESTS_PATH / 'interface' / 'ori-test'
ORI_PATH = TESTS_PATH.parent


def pytest_addoption(parser):
    parser.addoption("--controller", action="store", help="Juju controller")
    parser.addoption("--model", action="store", help="Juju model")
    parser.addoption("--keep", action="store_true",
                     help="Keep controller and / or model")


@pytest.fixture(scope='session')
def check_deps(autouse=True):
    missing = []
    for dep in ('microk8s', 'juju', 'charm', 'charmcraft', 'juju-wait'):
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
        run(['python', 'setup.py', 'sdist', '-d', pydeps], check=True, cwd=src)
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
    shutil.copytree(REACTIVE_CHARM_PATH, src)
    wheelhouse_txt = wheelhouse_path.read_text()
    wheelhouse_txt = wheelhouse_txt.format(pydeps=pydeps)
    wheelhouse_path.write_text(wheelhouse_txt)

    run(['charm', 'build', '-d', builds_path, src], check=True)
    return dst


@pytest.fixture(scope='session')
def ops_charm(pydeps, charms_path, builds_path):
    src = charms_path / 'ops-charm'
    dst = builds_path / 'ops-charm.charm'
    requirements_path = src / 'requirements.txt'

    # parameterize requirements.txt to allow installation of built pydeps
    shutil.copytree(OPS_CHARM_PATH, src)
    requirements_txt = requirements_path.read_text()
    requirements_txt = requirements_txt.format(pydeps=pydeps)
    requirements_path.write_text(requirements_txt)

    run(['charmcraft', 'build', '-f', src], check=True, cwd=builds_path)
    return dst


class Juju:
    def __init__(self, controller=None, model=None):
        self.controller = controller
        self.model = model

    @property
    def full_model(self):
        return f'{self.controller}:{self.model}'

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

    def destroy_model(self, name):
        run(['juju', 'destroy-model', '-y', f'{self.controller}:{name}',
             '--destroy-storage'], check=True)

    def deploy(self, charm, num_units=1):
        if isinstance(charm, Path):
            charm = f'./{charm.relative_to(Path.cwd())}'
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
            run(['juju', 'wait', '-m', self.full_model, '-wt60'], check=True)
        except CalledProcessError:
            # run(['juju', 'status', '--format=json', '-m', self.full_model])
            # run(['juju', 'debug-log', '-m', self.full_model,
            #      '--replay', '--no-tail'])
            raise

    def status(self):
        res = run(['juju', 'status', '--format=json', '-m', self.full_model],
                  capture_output=True, check=True)
        return json.loads(res)


@pytest.fixture(scope='session')
def controller(request):
    if request.config.option.controller:
        yield request.config.option.controller
    else:
        juju = Juju()
        name = 'test-ori-' + uuid.uuid4().hex[:8]
        juju.bootstrap('microk8s', name)
        try:
            yield name
        finally:
            if not request.config.option.keep:
                juju.destroy_controller(name)


@pytest.fixture
def model(controller, request):
    if request.config.option.model:
        yield Juju(controller, request.config.option.model)
    else:
        juju = Juju(controller)
        name = request.function.__name__.replace('_', '-')
        juju.add_model(name)
        juju.model = name
        try:
            yield juju
        finally:
            if not request.config.option.keep:
                juju.destroy_model(name)
