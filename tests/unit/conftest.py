import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from ops.charm import CharmBase
from ops.testing import Harness

from charms.unit_test import patch_reactive


@pytest.fixture
def harness():
    charm_dir = Path(__file__).parents[1] / 'charms' / 'reactive-charm'
    metadata_file = charm_dir / 'metadata.yaml'
    sys_modules = sys.modules.copy()
    patch_reactive()
    harness = None
    try:
        import ops_reactive_interface as ori
        from charmhelpers.core import hookenv
        metadata = metadata_file.read_text()
        hookenv.metadata.return_value = yaml.safe_load(metadata)
        hookenv.charm_dir.return_value = charm_dir
        harness = Harness(CharmBase, meta=metadata)
        harness._charm_dir = charm_dir
        harness.begin()
        with patch.object(ori.InterfaceAPIFactory, '_charm', harness.charm):
            yield harness
    finally:
        if harness:
            harness.cleanup()
        sys.modules.clear()
        sys.modules.update(sys_modules)
