"""PDDL parsing.
"""
from copy import deepcopy

from pddlflatland.structs import (Type, Predicate, Function, LiteralConjunction, LiteralDisjunction,
                             Not, Anti, ForAll, Exists, When, Assign, ProbabilisticEffect,
                             TypedEntity, ground_literal, FLiteral, Equation, Greater, Less)

import re

FAST_DOWNWARD_STR = """
(define (problem {problem}) (:domain {domain})
  (:objects
        {objects}
  )
  (:init \n\t{init_state}
  )
  (:goal {goal})
)
"""

PROBLEM_STR = """
(define (problem {problem}) (:domain {domain})
  (:objects
        {objects}
  )
  (:goal {goal})
  (:init \n\t{init_state}
))
"""


class BasicOperator:
    """Class to hold an operator.
    """

    def __init__(self, name, params):
        self.name = name  # string
        self.params = params  # list of structs.Type objects

    def __str__(self):
        s = self.name + "(" + ",".join(self.params) + "): "
        s += " & ".join(map(str, self.preconds.literals))
        s += " => "
        s += " & ".join(map(str, self.effects.literals))
        return s


class Operator(BasicOperator):
    """Class to hold an operator.
    """

    def __init__(self, name, params, preconds, effects):
        super(Operator, self).__init__(name, params)
        self.preconds = preconds  # structs.Literal representing preconditions
        self.effects = effects  # structs.Literal representing effects

    def pddl_str(self):
        param_strs = [str(param).replace(":", " - ") for param in self.params]
        s = "\n\n\t(:action {}".format(self.name)
        s += "\n\t\t:parameters ({})".format(" ".join(param_strs))
        preconds_pddl_str = self._create_preconds_pddl_str(self.preconds)
        s += "\n\t\t:precondition (and {})".format(preconds_pddl_str)
        indented_effs = self.effects.pddl_str().replace("\n", "\n\t\t")
        s += "\n\t\t:effect {}".format(indented_effs)
        s += "\n\t)"
        return s

    def _create_preconds_pddl_str(self, preconds):
        all_params = set()
        precond_strs = []
        for term in preconds.literals:
            params = set(map(str, term.variables))
            if term.negated_as_failure:
                # Negative term. The variables to universally
                # quantify over are those which we have not
                # encountered yet in this clause.
                universally_quantified_vars = list(sorted(
                    params - all_params))
                precond = ""
                for var in universally_quantified_vars:
                    precond += "(forall ({}) ".format(
                        var.replace(":", " - "))
                precond += "(or "
                for var in universally_quantified_vars:
                    var_cleaned = "?" + var[:var.find(":")]
                    for param in list(sorted(all_params)):
                        param_cleaned = "?" + param[:param.find(":")]
                        precond += "(not (Different {} {})) ".format(
                            param_cleaned, var_cleaned)
                precond += "(not {}))".format(term.positive.pddl_str())
                for var in universally_quantified_vars:
                    precond += ")"
                precond_strs.append(precond)
            else:
                # Positive term.
                all_params.update(params)
                precond_strs.append(term.pddl_str())

        return "\n\t\t\t".join(precond_strs)


class DurationOperator(BasicOperator):
    def __init__(self, name, params, duration, conditions, effects):
        super(DurationOperator, self).__init__(name, params)
        self.duration = duration
        self.conditions = conditions
        self.effects = effects

    def pddl_str(self):
        param_strs = [str(param).replace(":", " - ") for param in self.params]
        s = "\n\n\t(:durative-action {}".format(self.name)
        s += "\n\t\t:parameters ({})".format(" ".join(param_strs))
        s += "\n\t\t:duration ({0} ?duration {1})".format(" ".join(self.duration[0], self.duration[1]))
        conditions_pddl_str = self._create_preconds_pddl_str(self.conditions)
        s += "\n\t\t:condition (and {})".format(conditions_pddl_str)
        indented_effs = self.effects.pddl_str().replace("\n", "\n\t\t")
        s += "\n\t\t:effect {}".format(indented_effs)
        s += "\n\t)"
        return s

    def _create_preconds_pddl_str(self, conditions):
        all_params = set()
        condition_strs = []
        for term in conditions.literals:
            params = set(map(str, term.variables))
            if term.negated_as_failure:
                # Negative term. The variables to universally
                # quantify over are those which we have not
                # encountered yet in this clause.
                universally_quantified_vars = list(sorted(
                    params - all_params))
                condition = ""
                for var in universally_quantified_vars:
                    condition += "(forall ({}) ".format(
                        var.replace(":", " - "))
                condition += "(or "
                for var in universally_quantified_vars:
                    var_cleaned = "?" + var[:var.find(":")]
                    for param in list(sorted(all_params)):
                        param_cleaned = "?" + param[:param.find(":")]
                        condition += "(not (Different {} {})) ".format(
                            param_cleaned, var_cleaned)
                condition += "(not {}))".format(term.positive.pddl_str())
                for var in universally_quantified_vars:
                    condition += ")"
                condition_strs.append(condition)
            else:
                # Positive term.
                all_params.update(params)
                condition_strs.append(term.pddl_str())

        return "\n\t\t\t".join(condition_strs)


class PDDLParser:
    """PDDL parsing class.
    """

    def _parse_into_literal(self, string, params, is_effect=False, is_func=False):
        """Parse the given string (representing either preconditions or effects)
        into a literal. Check against params to make sure typing is correct.
        """
        # assert string[0] == "("
        # assert string[-1] == ")"
        if string.startswith("(and") and string[4] in (" ", "\n", "("):
            clauses = self._find_all_balanced_expressions(string[4:-1].strip())
            return LiteralConjunction([self._parse_into_literal(clause, params,
                                                                is_effect=is_effect) for clause in clauses])
        if string.startswith("(or") and string[3] in (" ", "\n", "("):
            clauses = self._find_all_balanced_expressions(string[3:-1].strip())
            return LiteralDisjunction([self._parse_into_literal(clause, params,
                                                                is_effect=is_effect) for clause in clauses])
        if string.startswith("(forall") and string[7] in (" ", "\n", "("):
            new_binding, clause = self._find_all_balanced_expressions(
                string[7:-1].strip())
            new_name, new_type_name = new_binding.strip()[1:-1].split("-")
            new_name = new_name.strip()
            new_type_name = new_type_name.strip()
            assert new_name not in params, "ForAll variable {} already exists".format(new_name)
            params[new_name] = self.types[new_type_name]
            result = ForAll(self._parse_into_literal(clause, params, is_effect=is_effect),
                            TypedEntity(new_name, params[new_name]))
            del params[new_name]
            return result
        if string.startswith("(exists") and string[7] in (" ", "\n", "("):
            new_binding, clause = self._find_all_balanced_expressions(
                string[7:-1].strip())
            if new_binding[1:-1] == "":
                # Handle existential goal with no arguments.
                body = self._parse_into_literal(clause, params, is_effect=is_effect)
                return body
            variables = self._parse_objects(new_binding[1:-1])
            for v in variables:
                params[v.name] = v.var_type
            body = self._parse_into_literal(clause, params, is_effect=is_effect)
            result = Exists(variables, body)
            for v in variables:
                del params[v.name]
            return result
        if string.startswith("(probabilistic") and string[14] in (" ", "\n", "("):
            assert is_effect, "We only support probabilistic effects"
            lits = []
            probs = []
            expr = string[14:-1].strip()
            for match in re.finditer("(\d*\.?\d+)", expr):
                prob = float(match.group())
                subexpr = self._find_balanced_expression(expr[match.end():].strip(), 0)
                lit = self._parse_into_literal(subexpr, params, is_effect=is_effect)
                lits.append(lit)
                probs.append(prob)
            return ProbabilisticEffect(lits, probs)
        if string.startswith("(not") and string[4] in (" ", "\n", "("):
            clause = string[4:-1].strip()
            if is_effect:
                return Anti(self._parse_into_literal(clause, params, is_effect=is_effect))
            else:
                return Not(self._parse_into_literal(clause, params, is_effect=is_effect))
        # Durative Action
        if string.startswith("(at start") and string[9] in (" ", "\n", "("):
            return string[9:-1].strip()

        if string.startswith("(at end") and string[7] in (" ", "\n", "("):
            return string[7:-1].strip()

        if string.startswith("(over all") and string[9] in (" ", "\n", "("):
            return string[9:-1].strip()

        # Numeric Expression
        if (string.startswith("(=") or string.startswith("(-") or string.startswith("(+")) and \
                string[2] in (" ", "\n", "(") and not is_func:
            if string[2] == " ":
                index = 3
            else:
                index = 2
            node_string = self._find_balanced_expression(string.strip(), index).strip()
            if node_string.count('(') > 1:
                node = deepcopy(self._parse_into_literal(node_string, params, is_effect=is_effect,
                                                         is_func=False))
            else:
                node = deepcopy(self._parse_into_literal(node_string, params, is_effect=is_effect,
                                                         is_func=True))
            children_string = string[index + len(node_string): -1].strip()
            # (= (function int or float) (= (other function) int or float))
            if children_string.startswith('('):
                children_string = self._parse_into_literal(children_string, params, is_effect=is_effect,
                                                           is_func=True)
            # (= (function ?v) (int or float))
            if isinstance(node, FLiteral):
                form = string.strip()[1]
                form_exp = Equation()
                if form == ">":
                    form_exp = Greater()
                if form == "<":
                    form_exp = Less()
                node.function.form = form_exp
                node.function.value = deepcopy(children_string)
            return node

        if string.startswith("(when") and string[5] in (" ", "\n", "("):
            new_binding, clause = self._find_all_balanced_expressions(string[5:-1].strip())
            front = self._parse_into_literal(new_binding, params, is_effect=is_effect, is_func=False)
            backend = self._parse_into_literal(clause, params, is_effect=is_effect, is_func=False)
            return When(front, backend)

        if string.startswith("(assign") and string[7] in (" ", "\n", "("):
            index = 8
            parent_string = self._find_balanced_expression(string.strip(), index).strip()
            children_string = string[index + len(parent_string):-1].strip()
            if children_string.count('(') > 1:
                children = self._parse_into_literal(children_string, params, is_effect=is_effect, is_func=False)
            else:
                children = self._parse_into_literal(children_string, params, is_effect=is_effect, is_func=True)
            return Assign(parent_string, children)
        # The whole string is number
        if string.isdigit():
            return string

        if is_func:  # Function Expression
            string = string[1:-1].split()
            func_name, args = string[0], string[1:]

            typed_args = []
            assert func_name in self.functions, "Function {} is not defined".format(func_name)
            assert self.functions[func_name].arity == len(args), func_name
            for i, arg in enumerate(args):
                if arg not in params:
                    raise Exception("Argument {} not in params {}".format(arg, params))
                assert arg in params, "Argument {} is not in the params".format(arg)
                if isinstance(params, dict):
                    typed_arg = TypedEntity(arg, params[arg])
                else:
                    typed_arg = params[params.index(arg)]
                typed_args.append(typed_arg)

            return self.functions[func_name](*typed_args)

        else:  # Predicate Expression
            string = string[1:-1].split()
            pred, args = string[0], string[1:]
            typed_args = []
            # Validate types against the given params dict.
            assert pred in self.predicates, "Predicate {} is not defined".format(pred)
            assert self.predicates[pred].arity == len(args), pred
            for i, arg in enumerate(args):
                if arg not in params:
                    raise Exception("Argument {} not in params {}".format(arg, params))
                assert arg in params, "Argument {} is not in the params".format(arg)
                if isinstance(params, dict):
                    typed_arg = TypedEntity(arg, params[arg])
                else:
                    typed_arg = params[params.index(arg)]
                typed_args.append(typed_arg)
            _test = self.predicates[pred]
            return self.predicates[pred](*typed_args)

    def _parse_objects(self, objects):
        if self.uses_typing:
            # Assume typed objects are new-line separated.
            objects = objects.split("\n")
        else:
            # Untyped objects can be separated by any form of whitespace.
            objects = objects.split()
        obj_names = []
        obj_type_names = []
        for obj in objects:
            if not obj.strip():
                continue
            if self.uses_typing:
                obj_name, obj_type_name = obj.strip().split(" - ")
                obj_name = obj_name.strip()
                obj_type_name = obj_type_name.strip()
                if len(obj_name.split()) > 1:
                    for single_obj_name in obj_name.split():
                        obj_names.append(single_obj_name.strip())
                        obj_type_names.append(obj_type_name)
                else:
                    obj_names.append(obj_name)
                    obj_type_names.append(obj_type_name)
            else:
                obj_name = obj.strip()
                if " - " in obj_name:
                    obj_name, temp = obj_name.split(" - ")
                    obj_name = obj_name.strip()
                    assert temp == "default"
                obj_type_name = "default"
                obj_names.append(obj_name)
                obj_type_names.append(obj_type_name)
        to_return = set()
        for obj_name, obj_type_name in zip(obj_names, obj_type_names):
            if obj_type_name not in self.types:
                print("Warning: type not declared for object {}, type {}".format(
                    obj_name, obj_type_name))
                obj_type = Type(obj_type_name)
            else:
                obj_type = self.types[obj_type_name]
            to_return.add(TypedEntity(obj_name, obj_type))
        return sorted(to_return)

    def _purge_comments(self, pddl_str):
        # Purge comments from the given string.
        while True:
            match = re.search(r";(.*)\n", pddl_str)
            if match is None:
                return pddl_str
            start, end = match.start(), match.end()
            pddl_str = pddl_str[:start] + pddl_str[end - 1:]

    @staticmethod
    def _find_balanced_expression(string, index):
        """Find balanced expression in string starting from given index.
        """
        if string.isdigit():
            return string
        else:
            assert string[index] == "(", '"{}" in "{}"'.format(string[index], string)

        start_index = index
        balance = 1
        while balance != 0:
            index += 1
            symbol = string[index]
            if symbol == "(":
                balance += 1
            elif symbol == ")":
                balance -= 1
        return string[start_index:index + 1]

    @staticmethod
    def _find_all_balanced_expressions(string):
        """Return a list of all balanced expressions in a string,
        starting from the beginning.
        """

        assert string[0] == "(", string
        assert string[-1] == ")", string
        exprs = []
        index = 0
        start_index = index
        balance = 1
        while index < len(string) - 1:
            index += 1
            if balance == 0:
                exprs.append(string[start_index:index])
                # Jump to next "(".
                while True:
                    if string[index] == "(":  # Jump the line (跳到下一行开始)
                        break
                    index += 1
                start_index = index
                balance = 1
                continue
            symbol = string[index]
            if symbol == "(":
                balance += 1
            elif symbol == ")":
                balance -= 1
        assert balance == 0
        exprs.append(string[start_index:index + 1])
        return exprs


class PDDLDomain:
    """A PDDL domain.
    """

    def __init__(self, domain_name=None, types=None, type_hierarchy=None, predicates=None, functions=None,
                 operators=None, actions=None, operators_as_actions=False, is_probabilistic=False):
        # String of domain name.
        self.domain_name = domain_name
        # Dict from type name -> structs.Type object.
        self.types = types
        # Dict from supertype -> immediate subtypes.
        self.type_hierarchy = type_hierarchy
        # Dict from predicate name -> structs.Predicate object.
        self.predicates = predicates
        # Dict from function name -> structs.Function object.
        self.functions = functions
        # Dict from operator name -> Operator object (class defined above).
        self.operators = operators
        # Action predicate names (not part of standard PDDL)
        self.actions = actions
        self.operators_as_actions = operators_as_actions
        self.is_probabilistic = is_probabilistic

    @property
    def type_to_parent_types(self):
        """For convenience, create map of subtype to all parent types
        """
        return self._organize_parent_types()

    def determinize(self):
        """Determinize this operator by assuming max-probability effects.
        """
        assert self.is_probabilistic
        for op in self.operators.values():
            toremove = set()
            for i, lit in enumerate(op.effects.literals):
                if isinstance(lit, ProbabilisticEffect):
                    chosen_effect = lit.max()
                    if chosen_effect == "NOCHANGE":
                        toremove.add(lit)
                    else:
                        op.effects.literals[i] = chosen_effect
            for rem in toremove:  # remove effects where NOCHANGE is max-probability
                op.effects.literals.remove(rem)

    def _organize_parent_types(self):
        """Create dict of type -> parent types from type hierarchy
        """
        type_to_parent_types = {t: {t} for t in self.types.values()}
        for t in self.types.values():
            parent_types = self._get_parent_types(t)
            type_to_parent_types[t].update(parent_types)
        return type_to_parent_types

    def _get_parent_types(self, t):
        """Helper for organize parent types
        """
        parent_types = set()
        for super_type, sub_types in self.type_hierarchy.items():
            if t in sub_types:
                parent_types.add(super_type)
                parent_types.update(self._get_parent_types(super_type))
        return parent_types

    def write(self, fname):
        """Write the domain PDDL string to a file.
        """
        predicates = "\n\t".join([lit.pddl_str() for lit in self.predicates.values()])
        operators = "\n\t".join([op.pddl_str() for op in self.operators.values()])

        domain_str = """
(define (domain {})
  (:requirements :typing )
  (:types {})
  (:predicates {}
  )

  ; (:actions {})

  {}

)
        """.format(self.domain_name, self._types_pddl_str(),
                   predicates, " ".join(map(str, self.actions)), operators)

        with open(fname, 'w') as f:
            f.write(domain_str)

    def _types_pddl_str(self):
        if self.type_hierarchy:
            return "\n".join(["{} - {}".format(" ".join(
                self.type_hierarchy[k]), k) for k in self.type_hierarchy])
        else:
            return " ".join(self.types)


class PDDLDomainParser(PDDLParser, PDDLDomain):
    """PDDL domain parsing class.
    """

    def __init__(self, domain_fname, expect_action_preds=False, operators_as_actions=False, is_duration=False):
        # Parsing sets all domain fields
        PDDLDomain.__init__(self, operators_as_actions=operators_as_actions)

        self.domain_fname = domain_fname

        # Read files.
        with open(domain_fname, "r") as f:
            self.domain = f.read().lower()

        # Is this domain probabilistic?
        self.is_probabilistic = ("probabilistic" in self.domain)

        # Get action predicate names (not part of standard PDDL); Dongbox: "I thought isn't needed"
        # if expect_action_preds:
        #     self.actions = self._parse_actions()

        # Remove comments.
        self.domain = self._purge_comments(self.domain)
        assert ";" not in self.domain

        # Run parsing.
        self._parse_domain(is_duration=is_duration)

        if operators_as_actions:
            assert not expect_action_preds
            self.actions = self._create_actions_from_operators()
        elif not expect_action_preds:
            self.actions = set()

    def _parse_actions(self):
        start_ind = re.search(r"\(:actions", self.domain).start()
        actions = self._find_balanced_expression(self.domain, start_ind)
        actions = actions[9:-1].strip()
        return set(actions.split())

    def _create_actions_from_operators(self):
        actions = set()
        for name, operator in self.operators.items():
            types = [p.var_type for p in operator.params]
            action = Predicate(name, len(types), types)
            assert name not in self.predicates, "Cannot have predicate with same name as operator"
            self.predicates[name] = action
            actions.add(action)
        return actions

    def _parse_domain(self, is_duration):
        patt = r"\(domain(.*?)\)"
        self.domain_name = re.search(patt, self.domain).groups()[0].strip()
        self._parse_domain_types()
        self._parse_domain_predicates()
        self._parse_domain_functions()
        self._parse_domain_operators(is_duration=is_duration)  # whether duration action in domain or not

    def _parse_domain_types(self):
        match = re.search(r"\(:types", self.domain)
        if not match:
            self.types = {"default": Type("default")}
            self.type_hierarchy = {}
            self.uses_typing = False
            return
        self.uses_typing = True
        start_ind = match.start()
        types = self._find_balanced_expression(self.domain, start_ind)
        # Non-hierarchical types
        if " - " not in types:
            types = types[7:-1].split()
            self.types = {type_name: Type(type_name) for type_name in types}
            self.type_hierarchy = {}
        # Hierarchical types
        else:
            self.types = {}
            self.type_hierarchy = {}
            remaining_type_str = types[7:-1]
            while " - " in remaining_type_str:
                dash_index = remaining_type_str.index(" - ")
                s = remaining_type_str[dash_index:]
                super_start_index = dash_index + len(s) - len(s.lstrip()) + 2
                s = remaining_type_str[super_start_index:]
                try:
                    end_index_offset = min(s.index(" "), s.index("\n"))
                except ValueError:
                    end_index_offset = len(s)
                super_end_index = super_start_index + end_index_offset
                super_type_name = remaining_type_str[super_start_index:super_end_index]
                sub_type_names = remaining_type_str[:dash_index].split()
                # Add new types
                for new_type in sub_type_names + [super_type_name]:
                    if new_type not in self.types:
                        self.types[new_type] = Type(new_type)
                # Add to hierarchy
                super_type = self.types[super_type_name]
                if super_type in self.type_hierarchy:
                    self.type_hierarchy[super_type].update({self.types[t] for t in sub_type_names})
                else:
                    self.type_hierarchy[super_type] = {self.types[t] for t in sub_type_names}
                remaining_type_str = remaining_type_str[super_end_index:]
            assert len(remaining_type_str.strip()) == 0, "Cannot mix hierarchical and non-hierarchical types"

    def _parse_domain_predicates(self):
        start_ind = re.search(r"\(:predicates", self.domain)
        if not start_ind:
            return
        start_ind = start_ind.start()
        predicates = self._find_balanced_expression(self.domain, start_ind)
        predicates = predicates[12:-1].strip()
        predicates = self._find_all_balanced_expressions(predicates)
        self.predicates = {}
        for pred in predicates:
            pred = pred.strip()[1:-1].split("?")
            pred_name = pred[0].strip()
            # arg_types = [self.types[arg.strip().split("-")[1].strip()]
            #              for arg in pred[1:]]
            arg_types = []
            for arg in pred[1:]:
                if ' - ' in arg:
                    assert arg_types is not None, "Mixing of typed and untyped args not allowed"
                    assert self.uses_typing
                    arg_type = self.types[arg.strip().split("-")[1].strip()]
                    arg_types.append(arg_type)
                else:
                    assert not self.uses_typing
                    arg_types.append(self.types["default"])
            self.predicates[pred_name] = Predicate(
                pred_name, len(pred[1:]), arg_types)

    def _parse_domain_functions(self):
        # start_ind = re.search(r"\(:functions", self.domain).start()
        start_ind = re.search(r"\(:functions", self.domain)
        if not start_ind:
            return
        start_ind = start_ind.start()
        functions = self._find_balanced_expression(self.domain, start_ind)
        functions = functions[12:-1].strip()
        functions = self._find_all_balanced_expressions(functions)
        self.functions = {}
        for func in functions:
            func = func.strip()[1:-1].split("?")
            func_name = func[0].strip()
            # arg_types = [self.types[arg.strip().split("-")[1].strip()]
            #              for arg in pred[1:]]
            arg_types = []
            for arg in func[1:]:
                if ' - ' in arg:
                    assert arg_types is not None, "Mixing of typed and untyped args not allowed"
                    assert self.uses_typing
                    arg_type = self.types[arg.strip().split("-")[1].strip()]
                    arg_types.append(arg_type)
                else:
                    assert not self.uses_typing
                    arg_types.append(self.types["default"])
            self.functions[func_name] = Function(
                func_name, len(func[1:]), arg_types)

    def _parse_domain_operators(self, is_duration=False):
        if not is_duration:
            matches = re.finditer(r"\(:action", self.domain)
            self.operators = {}
            for match in matches:
                start_ind = match.start()
                op = self._find_balanced_expression(self.domain, start_ind).strip()
                patt = r"\(:action(.*):parameters(.*):precondition(.*):effect(.*)\)"
                op_match = re.match(patt, op, re.DOTALL)
                op_name, params, preconds, effects = op_match.groups()
                op_name = op_name.strip()
                params = params.strip()[1:-1].split("?")
                if self.uses_typing:
                    params = [(param.strip().split("-")[0].strip(),
                               param.strip().split("-")[1].strip())
                              for param in params[1:]]
                    params = [self.types[v]("?" + k) for k, v in params]
                else:
                    params = [param.strip() for param in params[1:]]
                    params = [self.types["default"]("?" + k) for k in params]
                preconds = self._parse_into_literal(preconds.strip(), params)
                effects = self._parse_into_literal(effects.strip(), params,
                                                   is_effect=True)
                self.operators[op_name] = Operator(
                    op_name, params, preconds, effects)
        else:
            matches = re.finditer(r"\(:durative-action", self.domain)
            self.operators = {}
            for match in matches:
                start_ind = match.start()
                op = self._find_balanced_expression(self.domain, start_ind).strip()
                patt = r"\(:durative-action(.*):parameters(.*):duration(.*):condition(.*):effect(.*)\)"
                op_match = re.match(patt, op, re.DOTALL)
                op_name, params, duration, conditions, effects = op_match.groups()
                op_name = op_name.strip()
                # params parsing
                params = params.strip()[1:-1].split("?")
                if self.uses_typing:
                    params = [(param.strip().split("-")[0].strip(),
                               param.strip().split("-")[1].strip())
                              for param in params[1:]]
                    params = [self.types[v]("?" + k) for k, v in params]
                else:
                    params = [param.strip() for param in params[1:]]
                    params = [self.types["default"]("?" + k) for k in params]
                # duration
                durations = duration.strip().split(" ")
                durations = (durations[0], durations[2])
                conditions = self._parse_into_literal(conditions.strip(), params)
                effects = self._parse_into_literal(effects.strip(), params,
                                                   is_effect=True)
                self.operators[op_name] = DurationOperator(
                    op_name, params, durations, conditions, effects)


class PDDLProblemParser(PDDLParser):
    """PDDL problem parsing class.
    """

    def __init__(self, problem_fname, domain_name, types, predicates, functions, action_names):
        self.problem_fname = problem_fname
        self.domain_name = domain_name
        self.types = types
        self.predicates = predicates
        self.functions = functions
        self.action_names = action_names
        self.uses_typing = not ("default" in self.types)

        self.problem_name = None
        # Set of objects, each is a structs.TypedEntity object.
        self.objects = None
        # Set of fluents in initial state, each is a structs.Literal.
        self.initial_state = None
        # structs.Literal representing the goal.
        self.goal = None

        ## Read files.
        with open(problem_fname, "r") as f:
            self.problem = f.read().lower()
        self.problem = self._purge_comments(self.problem)
        assert ";" not in self.problem

        ## Run parsing.
        self._parse_problem()

    def __str__(self):
        return self.pddl_string(objects=self.objects,
                                initial_state=self.initial_state,
                                problem_name=self.problem_name,
                                domain_name=self.domain_name,
                                goal=self.goal,
                                fast_downward_order=True)

    def _parse_problem(self):
        patt = r"\(problem(.*?)\)"
        self.problem_name = re.search(patt, self.problem).groups()[0].strip()
        patt = r"\(:domain(.*?)\)"
        domain_name = re.search(patt, self.problem).groups()[0].strip()
        assert domain_name == self.domain_name, "Problem file doesn't match the domain file!"
        self._parse_problem_objects()
        self._parse_problem_initial_state()
        self._parse_problem_goal()

    def _parse_problem_objects(self):
        start_ind = re.search(r"\(:objects", self.problem).start()
        objects = self._find_balanced_expression(self.problem, start_ind)
        objects = objects[9:-1].strip()
        if objects == "":
            self.objects = []
        else:
            self.objects = self._parse_objects(objects)

    def _parse_problem_initial_state(self):
        start_ind = re.search(r"\(:init", self.problem).start()
        init = self._find_balanced_expression(self.problem, start_ind)
        fluents = self._find_all_balanced_expressions(init[6:-1].strip())
        initial_lits = set()
        params = {obj.name: obj.var_type for obj in self.objects}
        for fluent in fluents:
            lit = self._parse_into_literal(fluent, params)
            if fluent.startswith("(="):
                if lit.function.name in self.action_names:
                    continue
                initial_lits.add(lit)
            else:
                if lit.predicate.name in self.action_names:
                    continue
                initial_lits.add(lit)
        self.initial_state = frozenset(initial_lits)

    def _parse_problem_goal(self):
        start_ind = re.search(r"\(:goal", self.problem).start()
        goal = self._find_balanced_expression(self.problem, start_ind)
        goal = goal[6:-1].strip()
        params = {obj.name: obj.var_type for obj in self.objects}
        self.goal = self._parse_into_literal(goal, params)

    @staticmethod
    def pddl_string(objects, initial_state, problem_name, domain_name, goal,
                    fast_downward_order=False):
        """Get the problem PDDL string for a given state.
        """
        objects_typed = "\n\t".join(list(sorted(map(lambda o: str(o).replace(":", " - "),
                                                    objects))))
        init_state = "\n\t".join([lit.pddl_str() for lit in sorted(initial_state)])

        problem_str = FAST_DOWNWARD_STR if fast_downward_order else PROBLEM_STR
        return problem_str.format(
            problem=problem_name,
            domain=domain_name,
            objects=objects_typed,
            init_state=init_state,
            goal=goal.pddl_str(),
        )

    @staticmethod
    def create_pddl_file(file_or_filepath, objects, initial_state, problem_name,
                         domain_name, goal, fast_downward_order=False):
        """Write the problem PDDL string for a given state into a file.
        """
        problem_str = PDDLProblemParser.pddl_string(
            objects=objects,
            initial_state=initial_state,
            problem_name=problem_name,
            domain_name=domain_name,
            goal=goal,
            fast_downward_order=fast_downward_order,
        )

        try:
            file_or_filepath.write(problem_str)
        except AttributeError:
            with open(file_or_filepath, 'w') as f:
                f.write(problem_str)

    def write(self, file_or_filepath, objects=None, initial_state=None, problem_name=None,
              domain_name=None, goal=None, fast_downward_order=False):
        """Write the problem PDDL string for a given state.
        """
        if objects is None:
            objects = self.objects
        if initial_state is None:
            initial_state = self.initial_state
        if problem_name is None:
            problem_name = self.problem_name
        if domain_name is None:
            domain_name = self.domain_name
        if goal is None:
            goal = self.goal

        return PDDLProblemParser.create_pddl_file(
            file_or_filepath,
            objects=objects,
            initial_state=initial_state,
            problem_name=problem_name,
            domain_name=domain_name,
            goal=goal,
            fast_downward_order=fast_downward_order,
        )


def parse_plan_step(plan_step, operators, action_predicates, objects, operators_as_actions=False):
    plan_step_split = plan_step.split()

    if operators_as_actions:
        # action_predicate = [a for a in action_predicates \
        #                     if a.name.lower() == plan_step_split[0].lower()]
        for a in action_predicates:
            if a.name.lower() == plan_step_split[0].lower()[1:]:
                action_predicate = a
                break
        object_names = plan_step_split[1:-2]
        args = []
        for name in object_names:
            match = None
            for o in objects:
                if o.name == name.replace(")", "").replace("(", ""):
                    match = o
                    break
            assert match is not None
            args.append(match)
        return action_predicate(*args)

    # Get the operator from its name
    operator = None
    for op in operators:
        if op.name.lower() == plan_step_split[0]:
            operator = op
            break
    assert operator is not None, "Unknown operator '{}'".format(plan_step_split[0])

    assert len(plan_step_split) == len(operator.params) + 1
    object_names = plan_step_split[1:]
    args = []
    for name in object_names:
        matches = [o for o in objects if o.name == name]
        assert len(matches) == 1
        args.append(matches[0])
    assignments = dict(zip(operator.params, args))

    for cond in operator.preconds.literals:
        if cond.predicate in action_predicates:
            ground_action = ground_literal(cond, assignments)
            return ground_action

    raise Exception("Unrecognized plan step: `{}`".format(str(plan_step)))


def parse_plan_step_lpg(plan_step, operators, action_predicates, objects, operators_as_actions=False):
    plan_step_split = plan_step.split()

    if operators_as_actions:
        # Return the plan from this way
        action_predicate = [a for a in action_predicates \
                            if a.name.lower() == plan_step_split[0][1:].lower()][0]
        object_names = [o.replace("(", "").replace(")", "") for o in plan_step_split[1:-2]]
        dc = [o.replace("[d:", "").replace("]", "").replace("c:", "") for o in plan_step_split[-2:]]
        # Rather return the split of the action than the literal
        cur_action = [action_predicate]
        cur_action.extend(object_names)
        cur_action.extend(dc)
        # cur_action===> 1.action 2-n.params -2:duration -1:action cost
        return cur_action

    # Get the operator from its name
    operator = None
    for op in operators:
        if op.name.lower() == plan_step_split[0]:
            operator = op
            break
    assert operator is not None, "Unknown operator '{}'".format(plan_step_split[0])

    assert len(plan_step_split) == len(operator.params) + 1
    object_names = plan_step_split[1:]
    args = []
    for name in object_names:
        matches = [o for o in objects if o.name == name]
        assert len(matches) == 1
        args.append(matches[0])
    assignments = dict(zip(operator.params, args))

    for cond in operator.preconds.literals:
        if cond.predicate in action_predicates:
            ground_action = ground_literal(cond, assignments)
            return ground_action

    raise Exception("Unrecognized plan step: `{}`".format(str(plan_step)))