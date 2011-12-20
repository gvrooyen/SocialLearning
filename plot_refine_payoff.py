from matplotlib.pylab import *

MEAN_PAYOFF = 10

def payoff_increment(r, r_max):
    """
    Calculate the increment in payoff due to the refinement r of an act
    """
    P_max = MEAN_PAYOFF * 50

    if r > r_max:
        r = r_max
    
    i = 0
    for j in range(1, r+1):
        i += 0.95 ** (r-j)
    
    i *= 0.05*P_max/(1.0 - (0.95 ** r_max))
    
    return int(round(i))

X = range(0,201)

for r_max in [200]:
    R = [payoff_increment(r, r_max) for r in X]
    plot(X,R)

show()
