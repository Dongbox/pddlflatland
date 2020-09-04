[![Build Status](https://travis-ci.com/tomsilver/pddlgym.svg?branch=master)](https://travis-ci.com/tomsilver/pddlgym)

# PDDLFlatland: PDDL &rarr; Flatland Competition
Fork from https://github.com/tomsilver/pddlgym

![Sokoban example](images/sokoban_example.gif?raw=true "Sokoban example")

**This library is under development by [Tom Silver](http://web.mit.edu/tslvr/www/) and [Rohan Chitnis](https://rohanchitnis.com/). Correspondence: <tslvr@mit.edu> and <ronuchit@mit.edu>.**

## Paper

Please see [our paper](https://arxiv.org/abs/2002.06432) describing the design decisions and implementation details behind PDDLGym.

## Status

**We support the following subset of PDDL1.2:**
- STRIPS
- Typing (including hierarchical)
- Quantifiers (forall, exists)
- Disjunctions (or)
- Equality
- Constants

Notable features that we do not currently support: conditional effects, action costs, derived predicates.

Several PDDL environments are included, such as:
- Sokoban
- Depot
- Blocks
- Keys and Doors
- Towers of Hanoi
- Snake
- Fridge
- Gripper
- Ferry
- Elevator
- TSP
- "Minecraft"
- "Rearrangement"
- "Travel"
- "Baking"

(Environments in quotes indicate ones that we made up ourselves. Unquoted environments are standard ones whose PDDL files are available online, with light modifications to support our interface.)

We also support probabilistic effects, specified in the PPDDL syntax. Several PPDDL environments are included, such as:
- River
- Triangle Tireworld
- Exploding Blocks

Please get in touch if you are interested in contributing!

Sister packages: [pyperplan](https://github.com/aibasel/pyperplan) and [rddlgym](https://github.com/thiagopbueno/rddlgym).

## Installation

### Installing via pip

`pip install pddlgym`

### Installing from source (if you want to make changes to PDDLGym)

First, set up a virtual environment with Python 3. For instance, if you use [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/), you can simply run ``mkvirtualenv --python=`which python3` pddlgymenv``. Next, clone this repository, and from inside it run `pip install -e .`. Now you should able to run the random agent demos in `pddlgym/demo.py`. You should also be able to `import pddlgym` from any Python shell.

### Planner dependencies (optional)
To be able to run the planning demos in `pddlflatland/tests/test_flatland.py`, 

## Usage examples

### Hello, PDDLGym

## Citation

Please use this bibtex if you want to cite this repository in your publications:
```
@misc{silver2020pddlgym,
    title={PDDLGym: Gym Environments from PDDL Problems},
    author={Tom Silver and Rohan Chitnis},
    year={2020},
    eprint={2002.06432},
    archivePrefix={arXiv},
    primaryClass={cs.AI}
}
```
