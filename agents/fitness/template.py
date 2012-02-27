from moves import *
import math
import random

def move(roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
         canChooseModel, canPlayRefine, multipleDemes):
    try:

        if canChooseModel:
            if canPlayRefine:
                if multipleDemes:

                    ### mode_ORD
                    pass

                else:

                    ### mode_OR
                    pass

            else: # canChooseModel and (not canPlayRefine)
                if multipleDemes:

                    ### mode_OD
                    pass

                else:

                    ### mode_O
                    pass

        else: # not canChooseModel
            if canPlayRefine:
                if multipleDemes:

                    ### mode_RD
                    pass

                else:

                    ### mode_R
                    pass

            else: # (not canChooseModel) and (not canPlayRefine)
                if multipleDemes:

                    ### mode_D
                    pass

                else:

                    ### mode_nil
                    pass

    except:
        return (OBSERVE,)
    
    
def observe_who(exploiterData):
    try:

    except:
        return exploiterData
    

