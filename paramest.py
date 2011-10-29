from moves import *

class Hat:

    def __init__(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes,
                 currentDeme, canChooseModel, canPlayRefine, multipleDemes):
        
        # Estimate N_observe
        
        try:
            idx = historyMoves.index(OBSERVE)
        except ValueError:
            self.N_observe = 3   # Guess a reasonable default
        else:
            self.N_observe = 1
            current_round = historyRounds[idx]
            for round in historyRounds[idx+1:]:
                if round == current_round:
                    self.N_observe += 1
                else:
                    break
        
