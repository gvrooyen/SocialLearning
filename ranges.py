# The ParameterRange dictionary has a simulate.Simulate() parameter as key, and a tuple defining the constraints on the
# parameter. The first entry in the tuple is the type constraint; the following entries are range constraints. Here are
# typical examples:
#       'foo': (bool, None)         # 'foo' is Boolean, with no constraints (can be either True or False)
#       'foo': (bool, True)         # 'foo' is Boolean, and can only be True
#       'foo': (int, 0, 10)         # 'foo' is an integer, on the range 0 to 10 _inclusive_
#       'foo': (float, -1.0, 1.0)   # 'foo' is a floating-point number, on the range -1.0 to 1.0 _inclusive_

default_ParameterRange = {'mode_spatial': (bool, None),
                  'mode_cumulative': (bool, None),
                  'mode_model_bias': (bool, None),
                  'N_observe': (int, 1, 10),
                  'P_c': (float, 0.001, 0.4),
                  'P_copyFail': (float, 0.0, 0.5),
                  'N_migrate': (int, 1, 20),
                  'r_max': (int, 10, 1000)
                 }

ParameterRange = {'mode_spatial': (bool, None),
                  'mode_cumulative': (bool, None),
                  'mode_model_bias': (bool, None),
                  'N_observe': (int, 5, 5),
                  'P_c': (float, 0.001, 0.4),
                  'P_copyFail': (float, 0.0, 0.5),
                  'N_migrate': (int, 10, 10),
                  'r_max': (int, 100, 100)
                 }


