from flwr_datasets import FederatedDataset
from datasets.utils.logging import disable_progress_bar
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from experiment import config


DEVICE = torch.device("cpu")  # Try "cuda" to train on GPU
disable_progress_bar()


def preprocess(row: Dataset):

    features = torch.cat(
        [row["SepalLengthCm"], row["SepalWidthCm"], row["PetalLengthCm"], row["PetalWidthCm"]]
    ).flatten()
    mapping = {
        "Iris-setosa": [1, 0, 0],
        "Iris-versicolor": [0, 1, 0],
        "Iris-virginica": [0, 0, 1],
    }
    label = torch.tensor(mapping[row["Species"][0]], dtype=torch.float64)

    return features.to(DEVICE), label.to(DEVICE)


def load_datasets(partition_id: int):
    fds = FederatedDataset(dataset="scikit-learn/iris", partitioners={"train": config.NUM_NODES}, shuffle=True)
    partition = fds.load_partition(partition_id)

    partition.set_format(
        type="torch", columns=["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm", "Species"]
    )

    # Divide data on each node: 80% train, 20% test

    # partition.map(lambda x: preprocess(x))
    partition_train_test = partition.train_test_split(test_size=0.2, seed=42)
    # Create train/val for each partition and wrap it into DataLoader
    trainloader = DataLoader(partition_train_test["train"], shuffle=True)
    valloader = DataLoader(partition_train_test["test"])

    # testset = fds.load_split("test").with_transform(apply_transforms)
    # testloader = DataLoader(testset, batch_size=BATCH_SIZE)
    return trainloader, valloader, None


def load_validation_dataset(partition_id: int, num_validators: int):
    """
    Dataset used by validator nodes.
    """
    fds = FederatedDataset(dataset="scikit-learn/iris", partitioners={"train": num_validators}, shuffle=True)
    partition = fds.load_partition(partition_id)

    partition.set_format(
        type="torch", columns=["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm", "Species"]
    )

    return DataLoader(partition, shuffle=True)


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.linear = nn.Linear(4, 3)

    def forward(self, x):
        return self.linear(x)


def train(net, trainloader, epochs=100, verbose=False):
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(net.parameters(), lr=0.01)
    net.train()

    for epoch in range(epochs):
        total_loss, correct, total = 0.0, 0, 0
        optimizer.zero_grad()
        for row in trainloader:
            features, target = preprocess(row)
            outputs = net(features)
            loss = criterion(outputs, target)
            # loguru.logger.debug(f"Loss: {loss.item()} outputs: {outputs} labels: {target}")
            total_loss += loss.item()
            loss.backward()
            total += 1
            # loguru.logger.debug(f"Predicted: {predicted} Label: {label}")
            correct += int(is_correct(outputs, target))

        optimizer.step()  # Update after processing all data
        epoch_loss = total_loss / len(trainloader.dataset)
        epoch_acc = correct / total
        if verbose:
            print(f"Epoch {epoch+1}: loss={epoch_loss:.4f}, accuracy={epoch_acc:.4f}")


def is_correct(predicted, target):
    return torch.argmax(predicted) == torch.argmax(target)


def test(net: nn.Module, testloader: DataLoader, verbose=False):
    """
    :return: Tuple of (loss, accuracy)
    """
    criterion = nn.CrossEntropyLoss()
    total_loss, correct, total = 0.0, 0, 0
    net.eval()
    with torch.no_grad():
        for row in testloader:
            features, labels = preprocess(row)
            outputs = net(features)
            total_loss += criterion(outputs, labels).item()
            total += 1
            correct += is_correct(outputs, labels)

    test_loss = total_loss / len(testloader.dataset)
    accuracy = correct / total
    if verbose:
        print(f"Test loss: {test_loss:.4f}, accuracy: {accuracy:.4f}")
    return test_loss, accuracy


def add_noise_to_weights(m: torch.Tensor):
    with torch.no_grad():
        if hasattr(m, "weight"):
            noise = ((torch.rand_like(m.weight) - 1) ** 2) * m.weight.mean()
            m.weight.add_(noise.to(DEVICE))


def flip_weights(m):
    with torch.no_grad():
        if hasattr(m, "weight"):
            m.weight.multiply_(-2)


def malicious_transforomation(m):
    return flip_weights(m)
