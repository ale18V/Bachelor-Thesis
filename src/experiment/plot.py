from typing import Optional
from matplotlib import pyplot as plt
import matplotlib

from experiment.metrics import MetricsStore


def plot(
    metrics: MetricsStore,
    path: Optional[str] = None,
    show: bool = False,
    title: Optional[str] = "Experiment Result"
) -> None:
    # After training completes, plot the accuracy
    plt.figure(figsize=(10, 6))
    accuracy_per_round, loss_per_round, malicious_ratio_per_round = zip(*metrics.get())
    x_axis = range(1, len(metrics) + 1)
    plt.plot(x_axis, accuracy_per_round, marker="o", linestyle="-", color="b", label="Accuracy")
    plt.plot(x_axis, loss_per_round, marker="o", linestyle="-", color="r", label="Loss")
    plt.plot(
        x_axis,
        malicious_ratio_per_round,
        marker="o",
        linestyle="--",
        color="g",
        label="Malicious contribution ratio",
    )
    # Add labels, title, and legend
    plt.title(title, fontsize=14)
    plt.xlabel("Round", fontsize=12)
    plt.ylabel("Accuracy", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=12)
    plt.tight_layout()

    if path:
        plt.savefig(path)
    if show:
        matplotlib.use("TkAgg")
        plt.show()
