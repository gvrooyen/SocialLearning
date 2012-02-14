"""
This module contains some examplary state graphs, that are likely to give good initial results when
simulated. These are intended to be used to seed the initial genetic programming population.
"""

import traits

def BifurcateDiscrete():

	traits = {}

	traits['PioneeringBi'] = traits.PioneeringBi.PioneeringBi()
	traits['PioneeringBi'].N_rounds = 3

	traits['Specialisation'] = traits.Specialisation.Specialisation()
	traits['SpecialisationB'] = traits.SpecialisationB.SpecialisationB()

	traits['DiscreteDistribution'] = traits.DiscreteDistribution.DiscreteDistribution()
	traits['DiscreteDistributionB'] = traits.DiscreteDistributionB.DiscreteDistributionB()
	traits['DiscreteDistributionC'] = traits.DiscreteDistributionC.DiscreteDistributionC()
	traits['DiscreteDistributionD'] = traits.DiscreteDistributionD.DiscreteDistributionD()
	traits['DiscreteDistributionE'] = traits.DiscreteDistributionE.DiscreteDistributionE()
	traits['DiscreteDistributionF'] = traits.DiscreteDistributionF.DiscreteDistributionF()
	traits['DiscreteDistributionG'] = traits.DiscreteDistributionG.DiscreteDistributionG()
	traits['DiscreteDistributionH'] = traits.DiscreteDistributionH.DiscreteDistributionH()

	state = [('PioneeringBi', ['Specialisation', 'SpecialisationB']),
	         ('Specialisation', ['DiscreteDistribution','DiscreteDistributionB','DiscreteDistributionC','DiscreteDistributionD']),
	         ('SpecialisationB', ['DiscreteDistributionE','DiscreteDistributionF','DiscreteDistributionG','DiscreteDistributionH']),
	         ('DiscreteDistribution', []),
	         ('DiscreteDistributionB', []),
	         ('DiscreteDistributionC', []),
	         ('DiscreteDistributionD', []),
	         ('DiscreteDistributionE', []),
	         ('DiscreteDistributionF', []),
	         ('DiscreteDistributionG', []),
	         ('DiscreteDistributionH', []),
	        ]
	
	return (traits, state)


def Simple():

	traits = {}

	traits['Pioneering'] = traits.Pioneering.Pioneering()
	traits['DiscreteDistribution'] = traits.DiscreteDistribution.DiscreteDistribution()

	state = [('Pioneering', ['DiscreteDistribution']),
		     ('DiscreteDistribution', [])
		    ]

	return (traits, state)


def SpecialPioneers():

	traits = {}

	traits['PioneeringBi'] = traits.Pioneering.Pioneering()
	traits['DiscreteDistribution'] = traits.DiscreteDistribution.DiscreteDistribution()
	traits['DiscreteDistributionB'] = traits.DiscreteDistributionB.DiscreteDistributionB()

	state = [('PioneeringBi', ['DiscreteDistribution', 'DiscreteDistributionB']),
		     ('DiscreteDistribution', []),
		     ('DiscreteDistributionB', [])
		    ]
		    
	return (traits, state)


examplars = [BifurcateDiscrete, Simple, SpecialPioneers]
