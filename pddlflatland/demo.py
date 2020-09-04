from collections import deque

from pddlflatland.core import PDDLEnv, PDDLFlatlandEnv
from pddlflatland.utils import run_random_agent_demo, run_planning_demo, \
    run_probabilistic_planning_demo, run_planning_fake_demo, run_planning_flatland_demo

import gym
import pddlflatland


def demo_random(env_name, render=True, problem_index=0, verbose=True):
    env = gym.make("PDDLEnv{}-v0".format(env_name.capitalize()))
    if not render: env._render = None
    env.fix_problem_index(problem_index)
    run_random_agent_demo(env, verbose=verbose, seed=0)


# def demo_fake():
#     domain_file = "./pddl/simpleTimeSat.pddl"
#     problem_dir = "./pddl/SimpleTime"
#     num_problems = 6
#     env = PDDLFakeEnv(domain_file, problem_dir)
#     for problem_index in range(num_problems):
#         env.fix_problem_index(problem_index)
#         actions = run_planning_fake_demo(env, 'lpg')
#         print(actions)


def demo_lpg_planing():
    from flatland.envs.rail_generators import sparse_rail_generator
    from flatland.envs.schedule_generators import sparse_schedule_generator
    from flatland.envs.observations import TreeObsForRailEnv
    n_agents = 1
    x_dim = 25
    y_dim = 25
    n_cities = 4
    max_rails_between_cities = 2
    max_rails_in_city = 3
    seed = 42
    # Observation parameters
    observation_tree_depth = 2

    domain_file = "./pddl/flatland.pddl"
    problem_dir = "./pddl/flatland"
    num_problems = 6

    tree_observation = TreeObsForRailEnv(max_depth=observation_tree_depth)

    env = PDDLFlatlandEnv(width=x_dim,
                          height=y_dim,
                          rail_generator=sparse_rail_generator(
                              max_num_cities=n_cities,
                              seed=seed,
                              grid_mode=False,
                              max_rails_between_cities=max_rails_between_cities,
                              max_rails_in_city=max_rails_in_city
                          ),
                          schedule_generator=sparse_schedule_generator(),
                          number_of_agents=n_agents,
                          obs_builder_object=tree_observation,
                          domain_file=domain_file,
                          problem_dir=problem_dir)

    for problem_index in range(num_problems):
        env.fix_problem_index(problem_index)
        run_planning_flatland_demo(env, 'lpg')


if __name__ == '__main__':
    from pddlflatland.parser import PDDLDomainParser

    # run_all()
    pddl = PDDLDomainParser("/home/dongbox/work/nips-flatland/pddlgym/pddlgym/pddl/flatland.pddl",
                            expect_action_preds=False, operators_as_actions=True)
    # print(pddl)
    # demo_ff_planning("blocks", 5, render=True, verbose=True)
    # demo_lpg_planing()
