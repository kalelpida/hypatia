import pickle
import sys, os
import numpy as np


RESFIC = "resultats.pickle"
EXPE_LOG_BASE_DIR = "../papier2/sauvegardes/paramTester/"

def fonction():
    """Fonction objectif"""
    ifobj=0
    util_liens = maj_resultats()
    for lien, res in util_liens.items():
        ifobj+=1/res.val
    return 1/ifobj

class Resultat():
    VERSION = '0' # à modifier chaque fois qu'un paramètre ci-dessous est ajouté/modifié
    INSTANT = '7s'
    DUREE = '20ms'
    def __init__(self, **kwargs):
        dico_typelien_utilisation=kwargs['dico_typelien_utilisation']
        self.val3q = {nom : np.quantile(vals, 0.75) for nom, vals in dico_typelien_utilisation.items()}
        self.valmax = {nom : np.max(vals) for nom, vals in dico_typelien_utilisation.items()}
    
    @classmethod
    def attributs(cls):
        return [(nom, val) for (nom, val) in cls.__dict__.items() if all(map(str.isupper, nom))]

    @classmethod
    def attributs_ns(cls):
        def to_ns(val):
            res=val.replace('ms', "e6")
            res=res.replace('µs', "e3")
            res=res.replace('ns', '')
            res=res.replace('s', 'e9')
            return int(eval(res))
        return {nom.lower(): to_ns(val) for (nom, val) in cls.attributs()}

def maj_resultats():
    changement=False
    if os.path.isfile(RESFIC):
        with open(RESFIC, 'rb') as f:
            dico_res = pickle.load(f)
            if dico_res == None:
                dico_res={}
    else:
        dico_res={}
    for dos in list(dico_res.keys()):
        dircomplet=os.path.join(EXPE_LOG_BASE_DIR,dos)
        if dos in dico_res and not os.path.isdir(dircomplet):
            changement=True
            del dico_res[dos]
    for dos in os.listdir(EXPE_LOG_BASE_DIR):
        dircomplet=os.path.join(EXPE_LOG_BASE_DIR,dos)
        if os.path.isdir(dircomplet) and ( dos not in dico_res or dico_res[dos].attributs() != Resultat.attributs()):
            changement=True
            dico_typelien_utilisation = collecte_utilisation(dircomplet, **Resultat.attributs_ns())
            dico_res[dos] = Resultat(dico_typelien_utilisation=dico_typelien_utilisation)
    if changement:
        with open(RESFIC, 'wb') as f:
            pickle.dump(dico_res, f)
    
    return dico_res


def type_lien(info:str, idcom:int, src:int, dst:int, retour:bool)-> str:
    reponse = 'debit-if-'+info[:info.find('-')].lower()
    if reponse.endswith('gsl'):
        if src<dst:
            reponse+='&satellite'
        elif idcom%2 == retour:
            reponse+='&ue'
        else:
            reponse+='&gateway'
    else:
        assert reponse.endswith('isl')
    return reponse


def collecte_utilisation(dos, instant, duree, **kwargs):
    dico_links={}
    debut_ns, duree_ns = instant, duree
    #dico_links_src_gsl={} #list each gsl interface destinations # suppose these destinations won't vary in UTIL_INTERVAL (no routing table update)
    dico_links_type={}
    fin_interval_ns=debut_ns+duree_ns
    #find run directory
    run_trouve=False
    for glob in os.listdir(dos):
        if glob.startswith('run_loaded') and os.path.isdir(os.path.join(dos, glob)):
            assert not run_trouve
            run_trouve = True
            run_glob= glob
    assert run_trouve
    # tx file
    txfic=os.path.join(dos, run_glob, "logs_ns3", "link.tx")
    assert os.path.isfile(txfic)

    with open(txfic, 'r') as f:
        while (l:=f.readline()):
            #30000,767,431,2,0,1502,1201599,GSL-tx
            deb, fin =l.find(','), l.rfind(',')
            if (t_ns:=int(l[:deb])) < debut_ns:
                continue
            elif t_ns>= fin_interval_ns:
                break
            info_lien=l[fin+1:].strip()
            src, dst, idcom, idseq, offset, payload, txtime_ns, isTCP, isRetour = eval(l[deb+1:fin])
            txtime_ns=min(txtime_ns,fin_interval_ns-t_ns)
            assert txtime_ns > 0
            #bandwidth is shared between destinations for gs links
            cle=(src, dst)
            if info_lien.startswith("GSL"):
                """
                if src in dico_links_src_gsl:
                    util_actuelle=max([dico_links[(src, unedst)] for unedst in dico_links_src_gsl[src]])
                    dico_links_src_gsl[src].add(dst)
                    for unedst in dico_links_src_gsl[src]-{dst}:
                        dico_links[(src, unedst)]=util_actuelle + txtime_ns/duree_ns
                    dico_links[(src, dst)]=util_actuelle # will be incremented just after
                else:
                    dico_links_src_gsl[src]={dst}
                """
                cle=(src, 'gsl')
            if cle in dico_links:
                dico_links[cle]+=txtime_ns/duree_ns
            else:
                dico_links[cle]=txtime_ns/duree_ns
                tl=type_lien(info_lien, idcom, src, dst, isRetour)
                if tl in dico_links_type:
                    dico_links_type[tl].append(cle)
                else:
                    dico_links_type[tl] = [cle]
    resultats={tl : [] for tl in dico_links_type}
    for tl, liens in dico_links_type.items():
        for lien in liens:
            resultats[tl].append(dico_links[lien])
    return resultats



