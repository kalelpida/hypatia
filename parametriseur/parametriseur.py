from estimFonc import fonction
from paramExec import execution
from paramEval import evaluation, ecriture_params, lecture_params

PARAMS=["nb-UEs-sol", "gwTrafficControl", "debit-if-gsl&gateway", "debit-if-gsl&satellite", "debit-if-gsl&ue", "debit-if-isl"]
gwTrafficControl1 = {"type": "ns3::RRQueueDisc", "MaxSize": "QueueSize 15p", "ChildQueueDisc": "ns3::ITbfQueueDisc", "ChildRate": "DataRate 1Mbps"} 
gwTrafficControl2 = {"type": "ns3::FqCoDelQueueDisc", "MaxSize": "QueueSize 15p", "Interval": "String 200ms", "Target": "String 20ms"} 
valeurs=[[100, gwTrafficControl1, 60, 20, 1, 5], [200,gwTrafficControl2, 60, 20, 1, 5]]
def main():
    #selection param
    deja_testes=lecture_params()
    for vals in valeurs:
        dico_nvx_params=dict(zip(PARAMS, vals))
        z=list(map(lambda x: (x==dico_nvx_params), deja_testes.values()))
        if any(z):
            continue
        execution(dico_nvx_params)
        ecriture_params(dico_nvx_params)
    evaluation()

main()