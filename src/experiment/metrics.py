from typing import Optional


class MetricsStore(object):
    def __init__(self, metrics: Optional[list[tuple[float, float, float]]] = None) -> None:
        self._metrics: list[tuple[float, float, float]] = metrics if metrics is not None else []

    def update(self, accuracy: float, loss: float, malicious: float) -> None:
        self._metrics.append((accuracy, loss, malicious))

    def get(self) -> list[tuple[float, float, float]]:
        return [item for item in self._metrics]

    @property
    def accuracy(self) -> list[float]:
        return [metric[0] for metric in self._metrics]

    def __len__(self) -> int:
        return len(self._metrics)
