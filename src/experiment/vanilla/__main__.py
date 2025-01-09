from experiment.vanilla import cli
import flwr
import flwr.simulation
import torch

print(f"Flower {flwr.__version__} / PyTorch {torch.__version__}")

if __name__ == "__main__":
    cli()
