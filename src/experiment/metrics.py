from typing import Optional

type Metric = tuple[float, float, float]


class MetricsStore(object):
    def __init__(self, metrics: Optional[dict[int, Metric]] = None) -> None:
        self._metrics: dict[int, Metric] = metrics if metrics is not None else dict()

    def update(self, height: int, accuracy: float, loss: float, malicious: float) -> None:
        self._metrics[height] = (accuracy, loss, malicious)

    def get(self) -> tuple[list[int], list[tuple[float, float, float]]]:
        # return a tuple of heights, metrics
        heights, stats = zip(*sorted(self._metrics.items()))
        return list(heights), list(zip(*stats))

    def get_dict(self) -> dict[int, Metric]:
        return self._metrics.copy()

    @property
    def accuracy(self) -> list[float]:
        return [metric[0] for k, metric in sorted(self._metrics.items())]

    def __len__(self) -> int:
        return len(self._metrics)
