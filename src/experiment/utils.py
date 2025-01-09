import random


def get_malicious_actors_ids(num_nodes: int, seed: int, ratio: float) -> list[int]:
    random.seed(seed)
    return random.sample(range(num_nodes), k=int(ratio * num_nodes))


def get_validators_ids(num_nodes: int, malicious_actors: list[int], seed: int, num_validators: int) -> list[int]:
    random.seed(seed)
    return random.sample(list(filter(lambda i: i not in malicious_actors, range(num_nodes))), k=num_validators)
