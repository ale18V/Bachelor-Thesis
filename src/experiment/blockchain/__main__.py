import random
import time
from .cli import cli

if __name__ == "__main__":
    random.seed(time.time())
    cli()
