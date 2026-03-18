from app.services.adapters.demo import DemoBoardAdapter
from app.services.adapters.greenhouse import GreenhouseAdapter
from app.services.board_base import BaseBoardAdapter


ADAPTERS: dict[str, BaseBoardAdapter] = {
    "demo": DemoBoardAdapter(),
    "greenhouse": GreenhouseAdapter(),
}


def get_adapter(source: str) -> BaseBoardAdapter:
    return ADAPTERS.get(source, DemoBoardAdapter())

