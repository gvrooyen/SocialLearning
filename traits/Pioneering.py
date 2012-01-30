from solegene import *
from moves import *
import random

class Pioneering(Trait):

    @property
    def constraints(self):
        return ('initial')

    @property
    def evolvables(self):
        return {'N_rounds': (int, 1, 20)}
    
    def __init__(self):
        self.N_rounds = random.randint(1,20)

    def done(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        # True if the state has expired, or if other agents were exploiting (i.e., this individual isn't a pioneer)
        return ((roundsAlive >= self.N_rounds) or     
                ((len(historyActs) > 0) and (historyActs[0] > -1))
               )                
    
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
        