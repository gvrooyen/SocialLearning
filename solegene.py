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

render_template = \
"""# Automatically rendered agent code

from moves import *
import math

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

    # Traits (genes) associated with this genome. These are stored as a class-instance dictionary,
    # with classes as keys and specific instances as values. Some traits may be expressed (i.e. in
    # the genome's state graph) whereas others may be recessive and only occur in this dictionary.
    # During crossover or mutation, however, all genes are considered, not only those expressed in
    # the state graph.
    traits = {}

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


class Trait(object):
    __metaclass__ = ABCMeta

    @property
    def constraints(self):
        return ()

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
