from pddlgym.parser import PDDLDomainParser, PDDLProblemParser
from pddlgym.structs import Equation

if __name__ == '__main__':
    # Test parser
    domain_file = "/home/dongbox/work/nips-flatland/pddlgym/pddlgym/pddl/flatland.pddl"
    problem_file = "/home/dongbox/work/nips-flatland/pddlgym/pddlgym/pddl/flatland/problem.pddl"
    domain = PDDLDomainParser(domain_file)
    problem = PDDLProblemParser(problem_file, domain.domain_name, domain.types,
                                domain.predicates, domain.functions, domain.actions)
    # Initial
    # example 1: Add a position:c31 cause the update of the map maybe.(Usage of initial function)
    f_c31 = domain.functions['position']('c31')
    f_c31.function.form = Equation()
    f_c31.function.value = 23
    # example 2: Add an agent:agent2 to the position:c12 in the map.(Usage of initial predicate)
    p_a = domain.predicates['at']

    # Add initial definition to problem
    initial_state = set(problem.initial_state)
    initial_state.add(f_c31)
    initial_state.add(p_a('agent2', 'c12'))
    problem.initial_state = frozenset(initial_state)
    # Goal
    # example 3: Set the goal of position for agent:agent2 to position:c21.
    problem.goal.literals.append(p_a('agent2', 'c21'))
    print(problem)
