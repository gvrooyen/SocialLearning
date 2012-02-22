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
    """

    MAX_N_SEQ = 10

    @property
    def constraints(self):
        return ()

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
        interval = [self.Pi, self.Po, self.Pe, self.Pr]

        for i in xrange(1,4):
            interval[i] = interval[i-1] + interval[i]

        # Normalise the intervals
        if canPlayRefine:
            interval = [x/interval[-1] for x in interval]
        else:
            interval = [x/interval[-2] for x in interval]
        
        # If the repertoire is empty, only Pi or Po should be chosen:
        if len(repertoire) == 0:
            interval = [x/interval[-3] for x in interval]

        roll = random.random()

        if roll <= interval[0]:
            return (INNOVATE, )
        elif roll <= interval[1]:
            return (OBSERVE, )
        elif roll <= interval[2]:
            return (EXPLOIT, max(repertoire, key=repertoire.get))
        elif (roll <= interval[3]) and canPlayRefine:   # Add the sanity check in case of rounding errors
            return (REFINE, max(repertoire, key=repertoire.get))
        else:
            # Catch-all for rounding errors
            return (EXPLOIT, max(repertoire, key=repertoire.get))


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
        The default behavior is to randomly pick an evolvable, and recalculate it on the specified ranges.
        Subclasses should override this method to implement more directed mutation behaviour.
        """
        
        child = self.__class__()

        for prop in self.evolvables:
            setattr(child, prop, getattr(self, prop))

        if len(self.evolvables.keys()) > 0:
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
