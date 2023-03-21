from estimFonc import fonction
from paramExec import execution
from paramEval import evaluation, ecriture_params, lecture_params

PARAMS=["nb-UEs-sol", "gwTrafficControl", "debit-if-gsl&gateway", "debit-if-gsl&satellite", "debit-if-gsl&ue", "debit-if-isl", "deteriorISL"]
gwTrafficControl1 = {"type": "ns3::RRQueueDisc", "MaxSize": "QueueSize 60p", "ChildQueueDisc": "ns3::ITbfQueueDisc", "ChildRate": "DataRate 2Mbps"} 
gwTrafficControl2 = {"type": "ns3::FqCoDelQueueDisc", "MaxSize": "QueueSize 60p", "Interval": "String 400ms", "Target": "String 200ms"} 
deterior_dico={ "sel": "topUtil50", "errModel": "gilbertElliottMdl-brstRate:0.1-brstSize:5-interval:0,7999ms"}
valeurs=[[100, gwTrafficControl1, 180, 80, 2, 20, deterior_dico], [100, gwTrafficControl2, 180, 80, 2, 20]]
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