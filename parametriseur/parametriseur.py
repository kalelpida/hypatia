from estimFonc import fonction
from paramExec import execution
from paramEval import evaluation, ecriture_params, lecture_params

PARAMS=["duree", "nb-UEs-sol","estimDelai", "debit-if-gsl&gateway", "debit-if-gsl&satellite", "debit-if-gsl&ue", "debit-if-isl", "debit-if-tl"]
vestimDelai = [ {"isl": 5, 'gsl': 4, 'extremite': 20 }, {"isl": 10, 'gsl': 8, 'extremite': 20 }, {"isl": 10, 'gsl': 8, 'extremite': 40 }, {"isl": 10, 'gsl': 8, 'extremite': 80 }, {"isl": 10, 'gsl': 8, 'extremite': 120 }, {"isl": 10, 'gsl': 8, 'extremite': 200 }    ]
#gwTrafficControl1 = {"type": "ns3::RRQueueDisc", "MaxSize": "QueueSize 60p", "ChildQueueDisc": "ns3::ITbfQueueDisc", "ChildRate": "DataRate 2Mbps"} 
#gwTrafficControl2 = {"type": "ns3::FqCoDelQueueDisc", "MaxSize": "QueueSize 60p", "Interval": "String 100ms", "Target": "String 300ms"} 
#deterior_dico={ "sel": "topUtil50", "errModel": "gilbertElliottMdl-brstRate:0.1-brstSize:5-interval:0,7999ms"}
valeurs=[[30, 90, delais, 150, 40, 2, 20, 150] for delais in vestimDelai]#, [300, gwTrafficControl2, 150, 80, 2, 20,deterior_dico, 3]]protocoles: 
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
