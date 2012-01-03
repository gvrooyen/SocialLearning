"""
solegene: A genetic programming framework for the Social Learning challenge.
"""

from abc import *
import random

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
    
    def predecessors(self):
        return '*'
    
    def successors(self):
        return '*'
    
    @abstractmethod
    def done(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        """
        Return True when the state associated with this trait has ended.
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
