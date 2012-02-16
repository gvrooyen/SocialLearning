"""
solegene: A genetic programming framework for the Social Learning challenge.
"""

from abc import *
import random
import inspect
import re
import string
import PythonTidy
import StringIO
import traits
import observe_strategies
import pkgutil
import md5
import simulate
import walkerrandom
import exemplars
import copy
import pygraphviz as dot
from agents.rendered.exceptions import *

import cloud.mp as cloud    # Simulate cloud processing locally
# import cloud

MAX_STATE_RECURSION = 16

render_template = \
"""# Automatically rendered agent code

from moves import *
import math
import random

last_state = None
last_state_matrix = None

def move(roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
         canChooseModel, canPlayRefine, multipleDemes):
$move
    
def observe_who(exploiterData):
$observe
"""

state_calc_template = \
"""
def traverse_states(state_matrix, state_idx = 0, entry_round = 0, recursion_depth = 0):
    if recursion_depth > %d:
        raise AgentError("Maximum state graph recursion reached (most likely due to an infinite state graph loop")
    done = state_matrix[state_idx][1](entry_round)
    if not done:
        return state_matrix[state_idx][0]
    else:
        # Traverse the state graph further by recursion. done[0] gives the number (1,2,3...) of the currently
        # considered state's output condition. state_matrix[state_idx][2][done[0]-1] translates into the
        # corresponding output state's index in state_matrix. done[1] is the round at which that next step
        # started running.
        return traverse_states(state_matrix, state_matrix[state_idx][2][done[0]-1], done[1], recursion_depth+1)

state = traverse_states(state_matrix)

""" % MAX_STATE_RECURSION

def indent(S,level):
    output = ""
    for line in S.split('\n'):
        output += (' '*4*level) + line + '\n'
    return output


class Genome(object):

    # Definition of the genome's state graph, as a list of trait-successor pairs in the following
    # format:
    #   [ (Trait1, [Successor1]),
    #     (Trait2, [Successor1, Successor2]),
    #     (Trait3, [])
    #   ]
    state = []

    # Maximum number of states allowed in a state graph (places a cap on bloat)
    MAX_STATES = 3

    # Traits (genes) associated with this genome. These are stored as a class-instance dictionary,
    # with classes as keys and specific instances as values. Some traits may be expressed (i.e. in
    # the genome's state graph) whereas others may be recessive and only occur in this dictionary.
    # During crossover or mutation, however, all genes are considered, not only those expressed in
    # the state graph.
    traits = {}

    # If a genome's code has been rendered, this will contain the hash and agent module name and path
    code_hash = None
    agent_name = None
    agent_path = None

    # Agent module, if rendered and imported
    agent_module = None

    # Current simulation for this genome, if active
    simulation = None

    observe_strategy = ''

    def __init__(self):
        """
        The default constructor creates a genome with a randomly initialised set of traits and state
        graph.
        """
        # The initialisation strategy is to populate the self.traits dictionary with a full complement
        # of all available traits, initialised with randomized evolvables (sampled on a uniform
        # distribution over their specified ranges). From these traits, between 1 and MAX_STATES
        # traits are then chosen to populate the state graph (self.state). Next, the state graph
        # is ordered in such a way that trait constraints are observed (e.g. 'initial' or 'terminal'),
        # possible discarding states if all constraints cannot be satisfied. Lastly, edges are connected
        # so that, if each state only has a single successor, the nodes (traits) are traversed linearly
        # (e.g. A -> B -> C). If some states have more than one successor, one successor is always chosen
        # randomly to linearly proceed to the next state, so that there is always an A -> B -> C progression
        # along some path in the graph. For other successors, the next state is chosen randomly (possibly
        # including the current state -- note that this would typically let a non-terminal state obtain
        # a terminal condition).

        # Import available traits one by one, and add them to the self.traits dictionary

        package = traits
        prefix = package.__name__ + '.'

        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
            T = __import__(modname, fromlist="*")
            T_name = T.__name__.split('.')[-1]      # The trait's unqualified name
            # A trait's default constructor handles the random initialisation
            self.traits[T_name] = getattr(T, T_name)()
        
        available_traits = self.traits.keys()
        initial_state = None
        terminal_states = []
        interem_states = []

        for i in xrange(0, random.randint(1,self.MAX_STATES)):
            if len(available_traits) == 0:
                break
            new_trait_name = random.choice(available_traits)
            available_traits.remove(new_trait_name)
            new_trait = self.traits[new_trait_name]

            if 'initial' in new_trait.constraints:
                # This possibly replaces any prior initial state that was sampled
                initial_state = new_trait
                if 'terminal' in new_trait.constraints:
                    # This state is constrained to be both initial and terminal, i.e. it can only be
                    # expressed as a solo state. Reset anything that's been selected so far, and
                    # exit the loop.
                    terminal_states = []
                    interem_states = []
                    break
            
            elif 'terminal' in new_trait.constraints:
                terminal_states.append(new_trait)
            
            else:
                interem_states.append(new_trait)
        
        # Next, add the available states to the state graph, initially with empty successor lists

        if initial_state != None:
            self.state = [ (initial_state.__class__.__name__, []) ]
        elif len(interem_states) > 0:
            new_state = random.choice(interem_states)
            interem_states.remove(new_state)
            self.state = [ (new_state.__class__.__name__, []) ]
        elif len(terminal_states) > 0:
            new_state = random.choice(terminal_states)
            terminal_states.remove(new_state)
            self.state = [ (new_state.__class__.__name__, []) ]
        else:
            raise ImportError("No valid traits found")
        
        # We add the interem states to the state graph next, followed by the terminal states

        for state in interem_states:
            self.state.append((state.__class__.__name__, []))
        for state in terminal_states:
            self.state.append((state.__class__.__name__, []))
        
        # For each output transition allowed by a state's associated trait, add a random state
        # as destination (excluding states with the 'initial' constraint)

        # TODO: Add support for valid_successors and valid_predecessors

        N = len(self.state)
        states_left_to_visit = [state.__class__.__name__ for state in interem_states+terminal_states]  # Add constraints

        for n in xrange(0, N-1):
            if len(states_left_to_visit) == 0:
                break
            for i in xrange(0, self.traits[self.state[n][0]].N_transitions):
                if len(states_left_to_visit) == 0:
                    break
                next_state = random.choice(states_left_to_visit)
                # states_left_to_visit.remove(next_state)
                self.state[n][1].append(next_state)
        
        self.observe_strategy = random.choice(observe_strategies.strategy)


    def render(self, debug = False):

        move = ""
        observe = indent(self.observe_strategy, 1)

        # Firstly, we capture the done() methods of the various traits as nested function definitions

        for (trait, successors) in self.state:
            move += "\n    def %s_done(entryRound):\n" % trait
            move += self.traits[trait].render_done()
        
        # It will be useful to build up a dictionary recording at which index each state occurs in the
        # state matrix

        state_map = {}

        for (idx, (trait, successors)) in enumerate(self.state):
            state_map[trait] = idx
        
        # Next, we need to try and find the current state of the agent. We do this by first building up a
        # state matrix with the following form:
        #
        #       state_matrix = [('Pioneering', Pioneering_done, [1]),
        #                       ('DiscreteDistribution', DiscreteDistribution_done, [])]
        #
        # Where each row is a possible state (with an unique state name), and is represented by a 3-tuple
        # consisting of the state's name, the state's _done() function, and a list that provides a mapping
        # between a state's M possible output conditions (1,2,3,...; note that this is 1-indexed) and the
        # corresponding output state's row in state_matrix.

        move += "\n    state_matrix = []\n"

        for (trait, successors) in self.state:
            move += "\n    state_matrix.append(('%s', %s_done, %s))\n" % (trait, trait,
                [state_map[t] for t in successors])
        
        move += indent(state_calc_template, 1)

        # If we're rendering with debugging information, add the current state matrix to the state_trace global variable

        if debug:
            move += ("\n    global last_state, last_state_matrix\n" +
                     "\n    last_state = state\n" +
                     "\n    last_state_matrix = state_matrix\n")

        # Next, output the code for each state

        prefix = ""
        for (trait, successors) in self.state:
            move += "\n\n    "+prefix+"if state == '%s':\n" % trait
            move += self.traits[trait].render_move() 
            prefix = "el"
        
        move += "\n\n    else:\n"
        move +=     "        raise AgentError('No such state: %s' % state)\n"
        
        result = string.Template(render_template)
        file_in = StringIO.StringIO(result.substitute(move = move, observe = observe))
        file_out = StringIO.StringIO()
        PythonTidy.tidy_up(file_in, file_out)
        return file_out.getvalue()

    
    def render_state(self):
        """
        Render the current state as an Graphviz AGraph() object.
        """
        G = dot.AGraph(strict=False, directed=True)
        for state in self.state:
            G.add_node(state[0])
            for edge in state[1]:
                G.add_edge(state[0],edge)
        return G


    def __add__(self, other):
        """
        Perform crossover between two individuals.

        Firstly, crossover is performed between all the individuals' traits. If one has a trait the other
        doesn't have, a mutated version is passed on to the child.

        Secondly, the state graphs are crossed over by selecting random crossover points, and joining the
        respective left and right graphs in such a way that a valid new graph is formed.
        """

        # Create a new child. Note that the default constructor initialises the child with random traits,
        # which allows it to discover traits that may not have been visible to its parents.
        child = Genome()

        # Pass over the parents' shared traits first
        for key in set(self.traits.keys()).intersection(other.traits.keys()):
            child.traits[key] = self.traits[key] + other.traits[key]
        
        # Pass over mutated versions of traits existing only in this parent
        for key in set(self.traits.keys()) - set(other.traits.keys()):
            child.traits[key] = +self.traits[key]
        
        # Pass over mutated versions of traits existing only in the other parent
        for key in set(other.traits.keys()) - set(self.traits.keys()):
            child.traits[key] = +other.traits[key]
        
        # The state graph isn't always a combination of the parents' state graphs. Instead, 1/3 of the time
        # it's an identical copy of the first parent's state graph; 1/3 of the time of the other parent.
        # For the remaining 1/3, it is a combined graph that truncates each of the parents' graphs at
        # crossover points, and splices them.
        #
        # This crossover strategy allows state graphs to evolve somewhat slower than the trait parameters.
        # Also, it provides some stability to "sensible" state graphs that may only need to evolve their
        # trait parameters further in order to dominate.

        crossover_strategy = random.randint()

        P1 = self.state
        P2 = other.state

        if crossover_strategy <= 1.0/3.0:
            child.state = P1
        elif crossover_strategy <= 2.0/3.0:
            child.state = P2
        else:

            # Create the parent subgraphs by selecting random crossover points
            P1 = P1[0:random.randint(1,len(P1))]
            P2 = P2[random.randint(0,len(P2)-1):len(P2)]

            print P1
            print P2

            # We'll ignore any edges pointing into the void for now. Let's join the two graphs first, and then
            # patch up any missing links. But first, we need to remove any duplicate states in the two graphs.

            for t in set([x[0] for x in P1]).intersection([x[0] for x in P2]):
                if random.random() < 0.5:
                    # Remove this state from the first parent
                    P1 = [x for x in P1 if x[0] != t]
                else:
                    # Remove this state from the second parent
                    P2 = [x for x in P2 if x[0] != t]
            
            child.state = P1 + P2

            valid_states = [x[0] for x in child.state]

            for (idx_s,s) in enumerate(child.state):
                for (idx_target,target) in enumerate(s[1]):
                    if target not in valid_states:
                        child.state[idx_s][1][idx_target] = child.state[random.randint(0,len(child.state)-1)][0]
            
            # TODO: Add a trimming function that removes unreachable states from the state graph (should speed up
            #       agent execution a bit)

        return child


    def __pos__(self):
        """
        Perform mutation on the individual genome. 50% of the time, this is just mutation of the individual
        traits. 50% of the time, an additional mutation of the state graph is performed, which may randomly
        be one of the following:
            - swapping of the position of two states
            - replacement of a state by an unused state
            - removal of a random leaf
            - replacement of a random transition
        """
        # Create a new child. Note that the default constructor initialises the child with random traits,
        # which allows it to discover traits that may not have been visible to its parents.
        child = Genome()

        child.state = copy.deepcopy(self.state)

        # Mutate the parent's traits
        for key in self.traits.keys():
            child.traits[key] = +self.traits[key]
        
        if random.random() > 0.5:
            mutation_type = random.choice(['swap', 'replace', 'remove', 'reroute'])
            if mutation_type == 'swap':
                # swapping means that any edges that were pointing towards the first state, now points towards
                # the second state, and vice versa:
                state1 = random.choice(self.state)[0]
                state2 = random.choice(self.state)[0]

                print("Swapping %s with %s" % (state1, state2))

                for (idx, state) in enumerate(child.state):
                    state_name = child.state[idx][0]
                    child.state[idx] = (state_name, [None if s==state1 else s for s in child.state[idx][1]])
                    child.state[idx] = (state_name, [state1 if s==state2 else s for s in child.state[idx][1]])
                    child.state[idx] = (state_name, [state2 if s==None else s for s in child.state[idx][1]])
            elif mutation_type == 'replace':
                # Select a victim
                state_idx = random.randint(0,len(child.state)-1)

                # Record the old state name -- we'll need to replace references to it
                old_state = child.state[state_idx][0]

                new_state = random.choice(child.traits.keys())

                # If a state with this name already exists in the graph, rip it out.
                for state in child.state:
                    if state[0] == new_state:
                        child.state.remove(state)
                        break
                
                # The index of the replacement state may have shifted now
                for (idx, state) in enumerate(child.state):
                    if state[0] == old_state:
                        state_idx = idx
                        break

                # Firstly, we need to fix any references TO this state, by replacing old_state with new_state
                for (idx, state) in enumerate(child.state):
                    child.state[idx] = (state[0], [new_state if s == old_state else s for s in state[1]])
                
                child.state[state_idx] = (new_state, child.state[state_idx][1])

                # Lastly, check that the number of outgoing edges on all states are still correct. If we have
                # too few, add random entries as necessary.
                
                for (idx, state) in enumerate(child.state):
                    while len(state[1]) > child.traits[state[0]].N_transitions:
                        child.state[idx][1].pop(random.randint(0,len(state[1])-1))
                    while len(state[1]) < child.traits[state[0]].N_transitions:
                        child.state[idx][1].append(random.choice(child.state)[0])
            
            elif mutation_type == 'remove':

                # Here we pluck out a random state, and then look through the state graph to replace all
                # reference to the state to a random new state

                if len(child.state) > 1:
                    # We can't remove the only state!
                    idx = random.randint(0, len(child.state)-1)
                    state_name = child.state[idx][0]
                    child.state.pop(idx)
                
                    for (idx, state) in enumerate(child.state):
                        if state_name in state[1]:
                            child.state[idx][1].remove(state_name)
                            child.state[idx][1].append(random.choice(child.state)[0])
            
            elif mutation_type == 'reroute':

                # Pick a random state, and if it has outgoing connections, randomly pick a new destination for one

                if len(child.state) > 2:
                    # Rerouting is really boring if we only have one or two states
                    idx = random.randint(0, len(child.state)-1)
                    state_name = child.state[idx][0]

                    num_edges = len(child.state[idx][1])
                    if num_edges > 0:
                        child.state[idx][1][random.randint(0,num_edges-1)] = random.choice(child.state)[0]

        
        print child.state

        return child



class Trait(object):
    __metaclass__ = ABCMeta

    @property
    def constraints(self):
        return ()
    
    @property
    def N_transitions(self):
        """
        Number of output transitions of a state corresponding to this trait (default 1)
        """
        return 1

    @property
    def eNoise(self):
        """
        Noisiness of crossover during evolution
        """
        return 0.333     # Noisiness of crossover during evolution

    @abstractproperty
    def evolvables(self):
        return {'property_name': (float, 0.0, 100.0)}
    
    def valid_predecessors(self):
        return '*'
    
    def valid_successors(self):
        return '*'
    
    @abstractmethod
    def done(self, entryRound,
             roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        """
        Return False/0 if the state associated with this trait is still active.

        The function has access to all the variables typically associated with an agent's move() function. Additionally,
        its first parameter is entryRound, the round of the agent's life when the state started (i.e. took its first
        move).

        If the state has ended, the function returns a tuple (n,r) with n corresponding to the number of the
        exit condition (1,2,3,...; 0 represents the current state itself) and r corresponding to the number
        of rounds that have elapsed in the agent's life after the state has ended. An ending state's r is the successor
        state's entryRound.

        Note that the return values can be treated as booleans, since 0 == False and 1 == True.
        """
        pass    
    
    @abstractmethod
    def move(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        """
        This is the exact code that should be played by the agent when its move() method is called. It has read access
        to the Trait descendant class's custom properties.
        """
        pass

    def __add__(self, other):
        """
        Crossover operator for two traits.
        The default behaviour is as follows:
            1. Check that both objects are of the same class, or that one is the subclass of the other
            2. Identify all shared evolvables between the two classes
            3. For each evolvable pair X1 and X2:
                    3.1 Calculate mu = (X1 + X2) / 2.
                    3.2 Calculate sigma = self.ENoise * abs(X2 - X1)
                    3.3 Cast the result to the correct type, and clip it to the prescribed limits
                    3.4 Pass on X = random.gauss(mu, sigma)
        It is assumed that both classes share the same ENoise factor, and the same type and limits for
        evolvable properties.
        """

        if issubclass(self.__class__, other.__class__):
            child = self.__class__()
        elif issubclass(other.__class__, self.__class__):
            child = other.__class__()
        else:
            raise TypeError("Cannot mate incompatible traits %s and %s" % (self.__class__, other.__class__))

        for prop in self.evolvables:
            if prop in other.evolvables:
                X1 = getattr(self, prop)
                X2 = getattr(other, prop)
                mu = (X1 + X2) / 2.
                sigma = self.eNoise * abs(X2 - X1)
                X = random.gauss(mu, sigma)
                if self.evolvables[prop][0] == int:
                    X = int(round(X))
                if X < self.evolvables[prop][1]:
                    X = self.evolvables[prop][1]
                elif X > self.evolvables[prop][2]:
                    X = self.evolvables[prop][2]
                setattr(child, prop, X)
        
        return child

    def __pos__(self):
        """
        Mutation operator for a single trait.
        The default behavior is to randomly pick an evolvable, and recalculate it on the specified ranges.
        Subclasses should override this method to implement more directed mutation behaviour.
        """
        
        child = self.__class__()

        for prop in self.evolvables:
            setattr(child, prop, getattr(self, prop))

        prop = random.choice(self.evolvables.keys())

        a = self.evolvables[prop][1]
        b = self.evolvables[prop][2]

        if self.evolvables[prop][0] == int:
            X = random.randint(a,b)
        elif self.evolvables[prop][0] == float:
            X = random.uniform(a,b)
        else:
            raise ValueError("Property %s <%s> is not mutatable" % (prop, type(prop))) 
        
        setattr(child, prop, X)

        return child

    def render_move(self):
        # This is a somewhat brittle routine, because it assumes that expressions being matched are not
        # substrings of other common expressions. This is mitigated somewhat by doing substring replacements
        # in order from longest to shortest, but a more robust rendering routine would use a more sophisticated
        # parser.

        source = inspect.getsource(self.move)
        R = re.compile(re.compile('move\(.*?\):(.*)', re.DOTALL))
        S = R.search(source).group(1)
        props = self.evolvables.keys()
        props.sort(key = lambda x: len(x), reverse = True)

        for p in props:
            S = re.sub('self.'+p, str(getattr(self, p)), S)

        return S

    def render_done(self):
        # This is a somewhat brittle routine, because it assumes that expressions being matched are not
        # substrings of other common expressions. This is mitigated somewhat by doing substring replacements
        # in order from longest to shortest, but a more robust rendering routine would use a more sophisticated
        # parser.

        source = inspect.getsource(self.done)
        R = re.compile(re.compile('done\(.*?\):(.*)', re.DOTALL))
        S = R.search(source).group(1)
        props = self.evolvables.keys()
        props.sort(key = lambda x: len(x), reverse = True)

        for p in props:
            S = re.sub('self.'+p, str(getattr(self, p)), S)

        return S

class Generation(object):

    POPULATION_SIZE = 100       # Population size of each GP generation
    DECIMATION_PERCENT = 0.2    # Weakest % of generation to decimate after D_ROUNDS rounds
    BROOD_SIZE = 20             # Suviving number of individuals that will be used to breed next generation
    D_ROUNDS = 1000             # Number of rounds to simulate in delta-estimation
    DEBUG = False
    P_CROSSOVER = 0.9
    P_MUTATION = 0.01
    PERFORMANCE_THRESHOLD = 500000  # Agents with a fitness beneath this threshold, are killed outright

    population = []
    sim_parameters = {}

    def __init__(self, sim_parameters = {}):
        # TODO: Add support for parameter ranges
        self.sim_parameters = sim_parameters
        for i in xrange(0, self.POPULATION_SIZE):
            new_genome = Genome()
            # Replace 20% of new individuals with "exemplars": pre-designed individuals that we believe will
            # perform well.
            if random.random() < 0.2:
                (self_traits, state) = random.choice(exemplars.exemplar_list)()
                new_genome.traits.update(self_traits)
                new_genome.state = state
            self.population.append(new_genome)
    

    def step(self):
        """
        Run fitness tests for the current generation, and evolve the next generation.
        """

        # Firstly, render code for all the genomes in the current population. Each genome owns its own
        # simulation object, because we want to interleave the simulations, running D_ROUNDS of simulation
        # rounds for all genomes, and killing off the weakest until BROOD_SIZE genomes remain.

        for genome in self.population:
            code = genome.render(debug = self.DEBUG)
            genome.code_hash = md5.md5(code).hexdigest()
            genome.agent_name = 'agent_' + genome.code_hash
            genome.agent_path = 'agents/rendered/' + genome.agent_name + '.py'
            f = open(genome.agent_path, 'w')
            f.write(code)
            f.close()
            genome.agent_module = __import__('agents.rendered.'+genome.agent_name, fromlist=['*'])
            genome.simulation = simulate.Simulate(**self.sim_parameters)
            genome.simulation.agent_move = genome.agent_module.move
            genome.simulation.agent_observe_who = genome.agent_module.observe_who
        
        jid = {}

        def job_callback(job):
            jid[job].simulation = cloud.result(job)
            print('Job %d completed with fitness %.2f.' % (job, 1.0*jid[job].simulation.total_payoff / jid[job].simulation.round))
        
        def job_error(job):
            print('Job %d terminated with an error.' % job)
       
        while len(self.population) > self.BROOD_SIZE:
            for genome in self.population:
                jid[cloud.call(genome.simulation.run, N_rounds = self.D_ROUNDS, return_self = True, 
                    _callback = [job_callback], _callback_on_error = [job_error], _fast_serialization = 0,
                    _type='c1')] = genome
            
            # Wait for all tasks to finish
            cloud.join(jid, ignore_errors=True)

            # for (job, genome) in zip(jid, self.population):
            #     genome.simulation = cloud.result(job)
            
            self.population.sort(reverse=True, key=lambda genome: 1.0 * genome.simulation.total_payoff)

            self.population = [genome for genome in self.population 
                               if genome.simulation.total_payoff >= self.PERFORMANCE_THRESHOLD]

            print([1.0 * genome.simulation.total_payoff / genome.simulation.round for genome in self.population])

            new_N = int(round(len(self.population) * (1. - self.DECIMATION_PERCENT)))
            if new_N < self.BROOD_SIZE:
                new_N = self.BROOD_SIZE
            
            # Let the fittest survive
            self.population = self.population[0:new_N]

        # Intialise the next generation
        next_population = []

        # Create a random parent generator, weighted by individuals' fitness
        parent = walkerrandom.Walkerrandom([genome.simulation.total_payoff for genome in self.population],
                                           self.population)

        while len(next_population) < self.POPULATION_SIZE:
            p1 = parent.random()
            r = random.random()
            if r < self.P_CROSSOVER:
                # Perform crossover mutation. Firstly, pick a second parent.
                p2 = parent.random()
                # Add the crossover of the two parents to the next generation.
                next_population.append(p1+p2)
            elif r < (self.P_CROSSOVER + self.P_MUTATION):
                # Add a mutated version of the current individual to the next generation
                next_population.append(+p1)
            else:
                # Let the chosen individual be reproduced identically to the next generation
                next_population.append(p1)

