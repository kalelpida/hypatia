from estimFonc import fonction
from paramExec import execution
from paramEval import evaluation, ecriture_params, lecture_params

PARAMS=["debit-if-gsl&ue", "debit-if-gsl&gateway", "debit-if-gsl&satellite", "debit-if-isl", "nb-UEs-sol"]
valeurs=[[1, 50, 5, 5, 50], [1, 50, 20, 3, 100]]
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