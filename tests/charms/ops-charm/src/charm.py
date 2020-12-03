#!/usr/bin/env python3

import json
import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus

from ori_test import ORITest

logger = logging.getLogger(__name__)


class OpsCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.giver = ORITest(self, 'give')
        self.taker = ORITest(self, 'take')
        self.sharer = ORITest(self, 'share')

        logger.info(f'is_leader: {self.unit.is_leader}')
        print(f'is_leader: {self.unit.is_leader}')
        if self.unit.is_leader:
            try:
                self.giver.send(self.app.name)
                self.sharer.send(self.app.name)
            except Exception:
                # XXX: temporarily work around weird hook error infinite loop
                import traceback
                logger.error(traceback.format_exc())
                return

        self.unit.status = ActiveStatus(json.dumps({
            'taker': {
                'relations': len(self.taker.relations),
                'is_changed': self.taker.is_changed,
                'received': self.taker.received,
            },
            'sharer': {
                'relations': len(self.sharer.relations),
                'is_changed': self.sharer.is_changed,
                'received': self.sharer.received,
            },
        }))


if __name__ == "__main__":
    main(OpsCharm)
