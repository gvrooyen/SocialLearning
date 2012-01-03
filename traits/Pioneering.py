from solegene import *
from moves import *

class Pioneering(Trait):

    @property
    def constraints(self):
        return ('initial')

    @property
    def evolvables(self):
        return {'N_rounds': (int, 1, 20)}
    
    def __init__(self):
        self.N_rounds = 10

    def done(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        return ((roundsAlive > self.N_rounds) or     # The state has expired
                (historyActs[0] > -1)                # Other agents were exploiting, so this individual isn't a pioneer
               )                
    
    def move(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        if 1 < roundsAlive <= self.N_rounds:
            return (INNOVATE, )
         
        else:    # This is the first round
            return (OBSERVE, )
