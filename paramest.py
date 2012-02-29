# Copyright (c) 2012 Stellenbosch University, 2012
# This source code is released under the Academic Free License 3.0
# See https://github.com/gvrooyen/SocialLearning/blob/master/LICENSE for the full text of the license.
# Author: G-J van Rooyen <gvrooyen@sun.ac.za>

"""
The paramest.Hat class provides algorithms to estimate N_observe, P_c and P_copyFail, given the variables
that are available to an agent during its move() function.
"""

from moves import *

class Hat:
    
    # Initially, all the parameters that can be estimated are set to None, pending lazy initialisation.
    # They will be calculated on the fly by their respective getters when needed.
    
    _N_observe = None
    _P_c = None
    _P_copyFail = None
    

    def __init__(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes,
                 currentDeme, canChooseModel, canPlayRefine, multipleDemes):

        # Store the received information as member variables. We will do the estimates on-the-fly as they are requested,
        # thereby minimising unnecessary processing.
        
        self._roundsAlive = roundsAlive
        self._repertoire = repertoire
        self._historyRounds = historyRounds
        self._historyMoves = historyMoves
        self._historyActs = historyActs
        self._historyPayoffs = historyPayoffs
        self._historyDemes = historyDemes
        self._currenteDeme = currentDeme
        self._canChooseModel = canChooseModel
        self._canPlayRefine = canPlayRefine
        self._multipleDemes = multipleDemes
        
    
    def N_observe(self):
        
        if not self._N_observe:
        
            # Estimate N_observe by counting the length of the first observation run we find.
            
            try:
                idx = self._historyMoves.index(OBSERVE)
            except ValueError:
                self._N_observe = 3   # Guess a reasonable default
            else:
                self._N_observe = 1
                current_round = self._historyRounds[idx]
                for round in self._historyRounds[idx+1:]:
                    if round == current_round:
                        self._N_observe += 1
                    else:
                        break
        
        return self._N_observe
        

    def P_c(self):
        
        if not self._P_c:
            
            # We estimate P_c by measuring its frequency: Number of payoff changes seen, divided by the number of
            # opportunities for change: i.e. the number of rounds between first seeing a payoff, and seeing it change.
            #
            # For the purpose of measuring payoff values and changes, INNOVATE and EXPLOIT are reliable, since they
            # provide exact measures of an act's payoff. OBSERVE has a measurement error, and cannot reliably be used
            # for P_c estimation (it may be possible to assume that the payoff seen through OBSERVE lies within the
            # standard deviation of the Poisson distribution around the actual payoff, but it is unclear at this stage
            # whether this will improve the estimate of P_c).
            #
            # Algorithm:
            # ~~~~~~~~~~
            # We cycle through the history of acts and Payoffs (for INNOVATE and EXPLOIT) and for each act we note:
            #
            #   1. The round at which it was first observed at the currently tracked payoff
            #   2. The round at which it was last observed at the currently tracked payoff
            #   3. The round in which the payoff changed
            #
            # When a payoff change is observed, we know that it occurred at some round after (2) and before or on (3)
            # above. Pick the round halfway between (2) and (3) (or exactly (3) if it immediately follows (2)) as the
            # best estimate for the round at which the payoff changed. Note that round as (1) for the next iteration,
            # and continue.
            
            # We record acts' payoff histories in a dictionary of tuples that can be annotated as follows:
            #     payoffLog[act] = (current_payoff, first_round_observed, last_round_observed)
            
            change_periods = []
            payoffLog = {}
            
            for i in xrange(0, len(self._historyRounds)):
                if ((self._historyMoves[i] == INNOVATE) or (self._historyMoves[i] == EXPLOIT)):
                    act = self._historyActs[i]
                    new_payoff = self._historyPayoffs[i]
                    round = self._historyRounds[i]
                    try:
                        (old_payoff, first_round_observed, last_round_observed) = payoffLog[act]
                    except KeyError:
                        # First time we've noted this act, so record it and move on
                        payoffLog[act] = (new_payoff, round, round)
                    else:
                        if new_payoff == old_payoff:
                            # Nothing's changed yet; record the observation and move on
                            payoffLog[act] = (new_payoff, first_round_observed, round)
                        else:
                            # We've observed a change! Now record its estimated period.
                            # If we first saw the act at R7, last saw it at that payoff at R20, and it is now:
                            #     R21: assume the change happened in R21 => period = (21 - 0 - 7) + 1
                            #     R23: assume the change happened in R22 => period = (23 - 1 - 7) + 1
                            #     R25: assume the change happened in R23 => period = (25 - 2 - 7) + 1
                            #      27                                 24              27 - 3 - 7
                            #      ...                                ...                 ...
                            #     Rx                                 Rx - ((Rx - R1 - 1) / 2) - R0 + 1
                            
                            est_transition_round = round - ((round - last_round_observed - 1) / 2)
                            change_periods.append(est_transition_round - first_round_observed)
                            payoffLog[act] = (new_payoff, est_transition_round, est_transition_round+1)
            
            if len(change_periods) > 0:
                self._P_c = 1.0 / (sum(change_periods) / len(change_periods))
            else:
                # Guess a reasonable default
                self._P_c = 0.001
        
        return self._P_c

    def P_copyFail(self):
        
        # Simple enough. Count the number of times we failed to copy a model through the OBSERVE action, and divided by
        # the total number of opportunities. If we've never tried to play OBSERVE, return a guess.
        #
        # This function cannot distinguish between copies that failed randomly, and failed due to N_observe exceeding
        # the available number of exploiters. This side effect may not be entirely undesirable -- it means that
        # P_copyFail() gives a basic estimate of the probability that an OBSERVE opportunity will fail, regardless of
        # the reason.
        
        if not self._P_copyFail:
            pass
            
