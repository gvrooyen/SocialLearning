from solegene import *
from moves import *
import random

class Pioneering(Trait):

    """
    Initial state to detect whether the agent is part of the very first generation of a population
    (the pioneers). This is done by playing OBSERVE on the first round. If no actions are observed,
    the agent assumes that all other agents where also playing OBSERVE, and that it is part of the
    pioneering group. If this is the case, it continues by playing INNOVATE for N_rounds rounds.
    Otherwise (if the agent is not a pioneer) the state ends.

    In this version of the trait, there is only one exit condition (if the state is not a pioneer
    or if N_rounds rounds have expired).
    """

    @property
    def constraints(self):
        return ('initial')

    @property
    def evolvables(self):
        return {'N_rounds': (int, 1, 20)}
    
    def __init__(self):
        self.N_rounds = random.randint(1,20)

    def done(self, entryRound,
             roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        assert entryRound == 0
        # Exit condition 1: The agent is a pioneer, and N_rounds rounds have elapsed
        if (roundsAlive >= self.N_rounds) and (historyActs[0] == -1):
            return (1,self.N_rounds)
        # Exit condition 2: We've tested, and the agent is not a pioneer
        elif (len(historyActs) > 0) and (historyActs[0] > -1):
            return (1,roundsAlive)
        # Otherwise, remain in the current state
        else:
            return 0
    
    def move(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        if roundsAlive == 0:
            return (OBSERVE, )
        else:
            return (INNOVATE, )


    def __pos__(self):
        child = Pioneering()
        if random.random() < 0.5:
            child.N_rounds = self.N_rounds - 1
        else:
            child.N_rounds = self.N_rounds + 1
        return child
        