# Copyright (c) 2012 Stellenbosch University, 2012
# This source code is released under the Academic Free License 3.0
# See https://github.com/gvrooyen/SocialLearning/blob/master/LICENSE for the full text of the license.
# Author: G-J van Rooyen <gvrooyen@sun.ac.za>

from solegene import *
from moves import *
import random

class InnovationBeat(Trait):

    """
    Attempt to synchronise the actions of agents by letting them play INNOVATE all at the same time, as the first move of a
    fixed-length cycle. This "innovation beat" should be detectable by a new agent who can play OBSERVE for a full cycle:
    The move where no models are observed (or very few with low payoffs) is most likely to be the the first round of the
    cycle. Even if the occasional mis-synchronisation occurs, this approach will allow most agents to be in sync, and let
    some exploit while others observe, and vice versa.
    
    In this version of InnovationBeat, agents randomly split themselves into one of two sequences to play each cycle. The
    length of the cycles, the move sequence in each cycle, and the probability with which either sequence is selected, are
    evolvable.
    
    The first move of each cycle is INNOVATE. The second move of the first cycle is EXPLOIT; for the second cycle the
    second move is OBSERVE. An agent chooses its second move at random to be either EXPLOIT or OBSERVE; this selects and
    identify its cycle for the rest of its life.
    
    The remainder of the moves in each sequence can be any of EXPLOIT, OBSERVE or REFINE. In a scenario where REFINE
    cannot be played, EXPLOIT is substituted.

    The approach to synchronisation used here can be seen as a form of quorum sensing, see e.g.
    http://arxiv.org/abs/1205.2952
    """

    MAX_N_SEQ = 10

    @property
    def constraints(self):
        return ('terminal')

    @property
    def N_transitions(self):
        return 0

    @property
    def evolvables(self):
        return {'N_Seq': (int, 2, self.MAX_N_SEQ),
                'seq_A': (list, 2, self.MAX_N_SEQ),
                'seq_B': (list, 2, self.MAX_N_SEQ),
                'Pa': (float, 0., 1.)}
    
    def __init__(self):
        self.N_Seq = random.randint(2, self.MAX_N_SEQ)
        self.seq_A = [INNOVATE, EXPLOIT]
        self.seq_B = [INNOVATE, OBSERVE]
        for i in xrange(3,11):
            next_A = random.choice([EXPLOIT, OBSERVE, REFINE])
            # We want to keep the list carefully synchronised. For example, we don't want both groups A and B
            # to play OBSERVE simultaneously. The invalid combinations are:
            #   OBSERVE - OBSERVE
            #   OBSERVE - REFINE
            #   REFINE - OBSERVE
            if next_A == OBSERVE:
                next_B = EXPLOIT
            elif next_A == REFINE:
                next_B = random.choice([EXPLOIT, REFINE])
            else:
                next_B = random.choice([EXPLOIT, OBSERVE, REFINE])
            self.seq_A.append(next_A)
            self.seq_B.append(next_B)
        self.Pa = random.random()

    def done(self, entryRound,
             roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        return False    # Terminal trait
    
    def move(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):

    # Firstly, we need to find a sequence of N_Seq OBSERVE actions, to decide which round is most likely to be
    # a sync round. We do this in a greedy way: if we see an OBSERVE round where no models (agents playing EXPLOIT)
    # were observe, we immediately assume that is a sync round. This has the added effect that pioneers (agents starting
    # this state in the very first round of a simulation) will start syncing on the first round.

        if roundsAlive < 2:
            return (OBSERVE,)
        else:
            start_idx = 0
            streak_found = False

            while not streak_found:
                # Try to find runs of the OBSERVE action. Note that multiple OBSERVE results may occur in a single round,
                # so we'll need to collapse these later
                try:
                    first_observe_idx = historyMoves[start_idx:].index(OBSERVE) + start_idx
                except ValueError:
                    # No OBSERVE actions remain in the history, so we need to create some
                    return (OBSERVE,)

                observe_payoffs = {}

                for idx in xrange(first_observe_idx, len(historyMoves)):
                    if historyMoves[idx] == OBSERVE:
                        round = historyRounds[idx]
                        try:
                            observe_payoffs[round] += historyPayoffs[idx]
                        except KeyError:
                            observe_payoffs[round] = historyPayoffs[idx]
                        if len(observe_payoffs) > self.N_Seq:
                            streak_found = True
                    else:
                        # The OBSERVE streak has ended before it was long enough; look for the next one.
                        start_idx = idx + 1
                        break
                else:
                    if not streak_found:
                        # We're midway through an OBSERVE streak; play the next round.
                        return (OBSERVE,)

            # Efficient trick to obtain both the minimum key and value in a single traversal
            import operator
            min_round, min_payoff = min(observe_payoffs.items(), key=operator.itemgetter(1))

            # The value of the minimum round allows us to determine at what offset the "innovation beat" occurs
            # relative to this individual's first round of life. We would like to later calculate
            # e.g. self.seq_A[(roundsAlive - offset) % 4] to determine what move in the sequence to play
            # recall that self.seq_A[0] is the INNOVATE round).
            #
            # If the min_round was found at round 13, and N_Seq == 4, offset must be 1, so that INNOVATE can
            # again be played at round 17, because (17 - 1) % 4 is zero.

            offset = (min_round) % self.N_Seq

            # The next thing we should check, is whether we've made the choice to be in group A or group B
            # yet. We do this by inspecting the moves after the OBSERVE streak (until they run out). The first
            # move that unambiguously corresponds to a move in one of the sequences (taking into account the
            # round and offset) is used to pick the sequence.
            #
            # Note that it typically doesn't matter if the OBSERVE streak was a coincidence from a previous
            # state, and that the "unambiguous correspondence" is also coincidental. It will in future associate
            # this individual with this state by the same analysis. (An exception to this assumption is if
            # a previous state deliberately plays similar OBSERVE sequences, which may disturb the A/B balance).

            last_observe_round = max(observe_payoffs.keys())

            seq = None

            for round in xrange(last_observe_round+1, historyRounds[-1]):
                idx = historyRounds.index(round)
                s = (round - offset) % self.N_Seq
                m = historyMoves[idx]

                # It's no use checking for unambiguous correspondence if the sequences play the same move at
                # this point
                if self.seq_A[s] != self.seq_B[s]:
                    if m == self.seq_A[s]:
                        seq = self.seq_A
                        break
                    elif m == self.seq_B[s]:
                        seq = self.seq_B
                        break
                    else:
                        # Keep on looking
                        pass

            if not seq:
                # We didn't find any evidence that we made a choice about a group to belong to yet. Pick one!
                seq = random.choice([self.seq_A, self.seq_B])

            next_move = seq[(roundsAlive - offset + 1) % self.N_Seq]

            if next_move == INNOVATE:
                return (INNOVATE,)
            elif next_move == OBSERVE:
                return (OBSERVE,)
            elif len(repertoire) > 0:
                if next_move == EXPLOIT:
                    return (EXPLOIT, max(repertoire, key=repertoire.get))
                elif next_move == REFINE:
                    if canPlayRefine:
                        return (REFINE, max(repertoire, key=repertoire.get))
                    else:
                        return (EXPLOIT, max(repertoire, key=repertoire.get))
            else:
                return (INNOVATE,)


    # We have to override the crossover and mutation operators, because the sequence lists need to be
    # treated carefully

    def __add__(self, other):
        """
        Crossover operator for two traits.
        """

        if issubclass(self.__class__, other.__class__):
            child = self.__class__()
        elif issubclass(other.__class__, self.__class__):
            child = other.__class__()
        else:
            raise TypeError("Cannot mate incompatible traits %s and %s" % (self.__class__, other.__class__))

        for prop in ['N_Seq', 'Pa']:
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

        # For the sequences, do a split-and-splice, then truncate the sequences to the maximum allowable length.
        # The first two elements of both sequence A and B must remain untouched.

        self_split = random.randint(2,self.MAX_N_SEQ)
        other_split = random.randint(2,self.MAX_N_SEQ)

        new_seq_A = self.seq_A[0:self_split] + other.seq_A[other_split:]
        new_seq_B = self.seq_B[0:self_split] + other.seq_B[other_split:]

        if len(new_seq_A) > self.MAX_N_SEQ:
            new_seq_A = new_seq_A[0:self.MAX_N_SEQ]
            new_seq_B = new_seq_B[0:self.MAX_N_SEQ]
        else:
            while len(new_seq_A) < self.MAX_N_SEQ:
                next_A = random.choice([EXPLOIT, OBSERVE, REFINE])
                # We want to keep the list carefully synchronised. For example, we don't want both groups A and B
                # to play OBSERVE simultaneously. The invalid combinations are:
                #   OBSERVE - OBSERVE
                #   OBSERVE - REFINE
                #   REFINE - OBSERVE
                if next_A == OBSERVE:
                    next_B = EXPLOIT
                elif next_A == REFINE:
                    next_B = random.choice([EXPLOIT, REFINE])
                else:
                    next_B = random.choice([EXPLOIT, OBSERVE, REFINE])
                new_seq_A.append(next_A)
                new_seq_B.append(next_B)

        child.seq_A = new_seq_A
        child.seq_B = new_seq_B
        
        return child

    def __pos__(self):
        """
        Mutation operator for a single trait.
        - N_Seq is mutated by increasing or decreasing it by one
        - Pa is mutated by randomly picking a new value on the range [0,1]
        - seq_A and seq_B are mutated by picking a random sequence position, and replacing the move pair
          at that position with a new valid pair
        """
        
        child = self.__class__()

        for prop in self.evolvables:
            setattr(child, prop, getattr(self, prop))

        if len(self.evolvables.keys()) > 0:
            prop = random.choice(self.evolvables.keys())

            a = self.evolvables[prop][1]
            b = self.evolvables[prop][2]
            c = getattr(self, prop)

            if prop == 'Pa':
                X = random.uniform(a,b)
                setattr(child, prop, X)
            elif prop == 'N_Seq':
                X = random.choice([-1, +1])
                setattr(child, prop, c+X)
            else:
                X = random.randint(0, self.MAX_N_SEQ-1)
                next_A = random.choice([EXPLOIT, OBSERVE, REFINE])
                # We want to keep the list carefully synchronised. For example, we don't want both groups A and B
                # to play OBSERVE simultaneously. The invalid combinations are:
                #   OBSERVE - OBSERVE
                #   OBSERVE - REFINE
                #   REFINE - OBSERVE
                if next_A == OBSERVE:
                    next_B = EXPLOIT
                elif next_A == REFINE:
                    next_B = random.choice([EXPLOIT, REFINE])
                else:
                    next_B = random.choice([EXPLOIT, OBSERVE, REFINE])
                child.seq_A[X] = next_A
                child.seq_B[X] = next_B

        return child
