import rungp
import cloud

# nice python rungp.py --debug -d ORd1 --mode_model_bias --mode_cumulative
jid = cloud.call(rungp.rungp, debug = True, d = 'ORd1', mode_model_bias = True, mode_cumulative = True)

cloud.join([jid])
