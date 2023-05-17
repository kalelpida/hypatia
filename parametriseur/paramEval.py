import yaml, os
import numpy as np

from estimFonc import maj_resultats

EXPE_LOG_BASE_DIR = "../papier2/sauvegardes/paramTester/"
INFO_FILE='paramTester.info'


def evaluation():
    print("evaluation")
    dico_util = maj_resultats()
    dico_params= lecture_params()
    for elt, util in sorted(dico_util.items()):
        print(f"\n\nExpérience {elt}\n")
        tableau(dico_params[elt], util.val3q, util.valmax)
        stats(util.dico_resultats_tcp, "TCP")

def tableau(dico_param, dico_util3q, dico_utilmax):
    print("|paramètres:")
    for p, val in dico_param.items():
        for vp in sorted(dico_util3q, key=lambda k: len(k), reverse=True):
            if vp.startswith(p):
                break
        else:#si le paramètre n'est pas utilisé dans la simu, ce n'est pas une constante
            print("|",p, val)
    print('\n|{: <40} | {: ^8} | {: ^8} | {: ^8}'.format("champ", "capacité", "util Q3", "util max"))
    strformat='|{: <40} | {: ^8.1f} | {: ^8.1f} | {: ^8.1f}'
    for vp, val3q in sorted(dico_util3q.items()):
        for p in sorted(dico_param, key=lambda k: len(k), reverse=True):
            if vp.startswith(p):
                print(strformat.format(vp, dico_param[p], dico_param[p]*val3q, dico_param[p]*dico_utilmax[vp]))
                break
        else:
            raise Exception (f"la valeur mesurée n'a pas d'information associée")

def stats(statistiques, titre):
    print('\nStatistiques {}\n|{: <40} | {: ^8}'.format(titre, "champ", "valeur"))
    for cpl in sorted(statistiques.items()):
        print("|{: <40} | {: ^8.2f}".format(*cpl))


def ecriture_params(dico_nvx_params, base_dir=EXPE_LOG_BASE_DIR, info_ficname=INFO_FILE):
    #write the configuration in the first directory which does not contain INFO_FILE. This should be the good one (assuming there is only one experiment per campaign)
    trouve=False
    assert os.path.isdir(base_dir)
    for dir in os.listdir(base_dir):
        dir_complet=os.path.join(base_dir, dir)
        if not os.path.isdir(dir_complet):
            continue
        info_fic=os.path.join(dir_complet, info_ficname)
        if not os.path.isfile(info_fic):
            assert not trouve
            trouve=True
            with open(info_fic, 'w') as f:
                yaml.dump(dico_nvx_params, f)


def lecture_params(base_dir=EXPE_LOG_BASE_DIR, info_ficname=INFO_FILE):
    params={}
    if not os.path.isdir(base_dir):
        print(f"{base_dir} n'existe pas")
        return params
    for dir in os.listdir(base_dir):
        dir_complet=os.path.join(base_dir, dir)
        if not os.path.isdir(dir_complet):
            continue
        info_fic=os.path.join(dir_complet, info_ficname)
        assert os.path.isfile(info_fic)
        with open(info_fic, 'r') as f:
            params[dir]=yaml.load(f, Loader=yaml.Loader)
    return params

def test():
    PARAMS=["debit-if-gsl&ue", "debit-if-gsl&gateway", "debit-if-gsl&satellite", "debit-if-isl", "nb-UEs-sol"]
    raise Exception('comment out this line before doing any mistake')
    test = {elt: np.random.randint(10) for elt in PARAMS}
    ecriture_params(test)

if __name__ == '__main__':
    test()