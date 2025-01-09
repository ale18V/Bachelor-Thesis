# Introduction
This project was developed as my bachelor thesis project at the University of Bologna. 
The aim is to provide a thoughtful implementation of federated learning over a blockchain network and compare it with classical client/server implementation.

The article provides an introduction to the relevant technologies and discusses the intrinsic problems of the client/server implementation of federated learning. Some of these can be solved by implementing it over a distributed, blockchain-based, network. The benefits/disadvantages of different architectural choices are also discussed.

The code contained in this project has the goal of implementing the architecture proposed in the article and comparing its performance with client/server federated learning.

The report is inside `article/` whereas the code is inside `packages/` and `src/`.

## Install
In order to run the experiment and the blockchain you'll need to setup the environment.

1. Install `uv` with `pip install uv`.
For alternative installation methods refer to https://github.com/astral-sh/uv.

2. Run `uv sync`: this will install the dependencies and setup the virtual environment.


## Run
The project is built to make running both the client/server experiment and the blockchain experiment effortlessly.
Each module offers a CLI with a couple of different options.
In particular, you can run simulations with either all honest nodes or some malicious nodes to check out how much this affects the performance of the model.

I'd suggest activating the virtual environment with `cd <PROJECT_ROOT> && source .venv/bin/activate`. 
However you can also run the python commands presented below with `uv run python3 etc...` without activating the venv.

### Client/Server
You can run the client/server simulation with
```sh
cd src/
python3 -m experiment vanilla
# or python3 -m experiment.vanilla
```
For the available options run `python3 -m experiment vanilla --help`.

### Blockchain
You can run the blockchain simulation with:
```sh
cd src/
python3 -m experiment blockchain
# or python3 -m experiment.blockchain
```
Checkout the options with `python3 -m experiment blockchain --help`.

### Blockchain Standalone
The blockchain can be ran standalone. This means that it won't have any federated learning features and no model will be trained.
You'll have to run a bootstrapping node first of all:
```sh
python3 -m blockchain bootstrap # checkout opts with --help
```
This node will wait until for your input before starting the chain (just press enter when you've launched all the other nodes).
You can run other nodes with:
```sh
# checkout opts with --help
# 7000 is the port and it can be different
python3 -m blockchain run 7000  
```

## Configuration
Configuration is a bit of a work-in-progress as the options that can be passed by CLI are limited.
In particular, to change parameters of the experiment such as:
- Number of nodes
- Number of malicious nodes and validators
- Machine learning parameters (number of local epochs and batch size)

You'll have to change the constants defined in `src/experiment/config.py`.

## Afterword
I will limit updates on this repository to configuration changes or bug fixing.
This is because major code changes would invalidate the results of the original report.
