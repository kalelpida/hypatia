from estimFonc import fonction
from paramExec import execution
from paramEval import evaluation, ecriture_params, lecture_params

PARAMS=["nb-UEs-sol", "tascconf", "debit-if-gsl&gateway", "debit-if-gsl&satellite", "debit-if-gsl&ue", "debit-if-isl"]
valeurs=[[100, "no-tc", 40, 20, 1, 5], [200,"no-tc", 40, 20, 1, 5]]
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