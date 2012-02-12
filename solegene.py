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
import pkgutil
import md5
import simulate
import walkerrandom
import pygraphviz as dot

import cloud.mp as cloud    # Simulate cloud processing locally
# import cloud

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
state_idx = 0
state_found = False

while not state_found:
    state_found = (state_matrix[state_idx][1] == None)
    if not state_found:
        if state_idx == state_matrix[state_idx][1]:
            # We're in a state loop; bail out
            state_found = True
        else:
            state_idx = state_matrix[state_idx][1]

state = state_matrix[state_idx][0]

"""

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
        # as destination

        # TODO: Add support for valid_successors and valid_predecessors

        # In the current implementation, each state may only be visited once

        N = len(self.state)
        states_left_to_visit = [state_name for (state_name, successors) in self.state]

        for n in xrange(0, N-1):
            if len(states_left_to_visit) == 0:
                break
            for i in xrange(0, self.traits[self.state[n][0]].N_transitions):
                if len(states_left_to_visit) == 0:
                    break
                next_state = random.choice(states_left_to_visit)
                states_left_to_visit.remove(next_state)
                self.state[n][1].append(next_state)


    def render(self, debug = False):

        move = ""
        observe = "    random.shuffle(exploiterData)\n    return exploiterData\n"

        # Firstly, we capture the done() methods of the various traits as nested function definitions

        for (trait, successors) in self.state:
            move += "\n    def %s_done():\n" % trait
            move += self.traits[trait].render_done()
        
        # It will be useful to build up a dictionary recording at which index each state occurs in the
        # state matrix

        state_map = {}

        for (idx, (trait, successors)) in enumerate(self.state):
            state_map[trait] = idx
        
        # Next, we need to try to find the current state of the agent. We do this by first evaluating
        # TraitX_done() for each item in the state list. The result is used to build a new dictionary of
        # sucessor states (with a successor of None if the particular state is not done yet). The successor
        # list is then traced to find the current state.

        move += "\n    state_matrix = []\n"

        for (trait, successors) in self.state:
            if successors == []:
                move += "\n    state_matrix.append(('%s', None))\n" % trait
            else:
                move += ("\n    s = %s_done()\n" % trait +
                          "    if s == 0:\n" +
                          "        state_matrix.append(('%s', None))\n" % trait +
                          "    else:\n"
                        )
                if len(successors) == 1:
                    move += "        state_matrix.append(('%s', %d))\n" % (trait, state_map[successors[0]])
                else:
                    move += "        state_matrix.append(('%s', s-1))\n" % trait
        
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

        # Create the parent subgraphs by selecting random crossover points
        P1 = self.state
        P2 = other.state

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
    def done(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        """
        Return True when the state associated with this trait has ended.

        Alternatively, if the state has multiple exit conditions, return the number of the exit condition. In this
        case, 0 corresponds to the current state (i.e. it has not ended yet), 1 to the first exit condition, 2 to
        the second exit condition, etc.

        Note that the boolean/integer return values are effectively interchangeable, since 0 == False and 1 == True.
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

    population = []
    sim_parameters = {}

    def __init__(self, sim_parameters = {}):
        # TODO: Add support for parameter ranges
        self.sim_parameters = sim_parameters
        for i in xrange(0, self.POPULATION_SIZE):
            self.population.append(Genome())
    

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
            print('Job %d completed with payoff %d.' % (job, jid[job].simulation.total_payoff))
       
        while len(self.population) > self.BROOD_SIZE:
            for genome in self.population:
                jid[cloud.call(genome.simulation.run, N_rounds = self.D_ROUNDS, return_self = True, 
                    _callback = [job_callback], _fast_serialization = 0, _type='c1')] = genome
            
            # Wait for all tasks to finish
            cloud.join(jid)

            # for (job, genome) in zip(jid, self.population):
            #     genome.simulation = cloud.result(job)
            
            self.population.sort(reverse=True, key=lambda genome: genome.simulation.total_payoff)
            print([genome.simulation.total_payoff for genome in self.population])

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

        while len(next_population) < POPULATION_SIZE:
            p1 = parent.random()
            r = random.random()
            if r < P_CROSSOVER:
                # Perform crossover mutation. Firstly, pick a second parent.
                p2 = parent.random()
                # Add the crossover of the two parents to the next generation.
                next_population.append(p1+p2)
            elif r < (P_CROSSOVER + P_MUTATION):
                # Add a mutated version of the current individual to the next generation
                next_population.append(+p1)
            else:
                # Let the chosen individual be reproduced identically to the next generation
                next_population.append(p1)

