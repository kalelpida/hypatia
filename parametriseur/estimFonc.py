import pickle
import sys, os, csv
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
    INSTANT = '10s'
    DUREE = '19999ms'
    def __init__(self, **kwargs):
        dico_typelien_utilisation=kwargs['dico_typelien_utilisation']
        self.dico_resultats_tcp=kwargs['dico_resultats_tcp']
        self.val3q = {nom : np.quantile(vals, 0.75) for nom, vals in dico_typelien_utilisation.items()}
        self.valmax = {nom : np.max(vals) for nom, vals in dico_typelien_utilisation.items()}
        self.infoparams=self.attributs_ns()
    
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
        if os.path.isdir(dircomplet) and ( dos not in dico_res or dico_res[dos].infoparams != Resultat.attributs_ns()):
            changement=True
            dico_typelien_utilisation = collecte_utilisation(dircomplet, **Resultat.attributs_ns())
            dico_resultats_tcp = collecte_resultats_tcp(dircomplet)
            dico_res[dos] = Resultat(dico_typelien_utilisation=dico_typelien_utilisation, dico_resultats_tcp=dico_resultats_tcp)
    if changement:
        with open(RESFIC, 'wb') as f:
            pickle.dump(dico_res, f)
    
    return dico_res


def type_lien(info:str, src:str, dst:str)-> str:
    modelien=info[:info.find('-')].lower()
    assert modelien in ('gsl', 'isl', 'tl')
    reponse = f'debit-if-{modelien}&{src}*{dst}'
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
        lecteur=csv.reader(f, delimiter=',')
        next(lecteur)#skip header. Sinon utiliser csv.DictReader
        for l in lecteur:
            #30000,767,431,2,0,1502,1201599,GSL-tx
            t_ns, src, typesrc, dst, typedst, idcom, idseq, offset, payload, txtime_ns, isTCP, isRetour, info_lien = l
            t_ns, src, dst, idcom, txtime_ns=int(t_ns), int(src), int(dst), int(idcom), int(txtime_ns)
            if t_ns < debut_ns:
                continue
            elif t_ns>= fin_interval_ns:
                break
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
                cle=(src, f'gsl-{typedst}')
            if cle in dico_links:
                dico_links[cle]+=txtime_ns/duree_ns
            else:
                dico_links[cle]=txtime_ns/duree_ns
                tl=type_lien(info_lien, typesrc, typedst)
                if tl in dico_links_type:
                    dico_links_type[tl].append(cle)
                else:
                    dico_links_type[tl] = [cle]
    resultats={tl : [] for tl in dico_links_type}
    for tl, liens in dico_links_type.items():
        for lien in liens:
            resultats[tl].append(dico_links[lien])
    return resultats

def TCPRes(ligne):
    dico={}
    commId, src, dst, taille_o, deb_ns, fin_ns, duree_ns, tx_o, fini, groupe = ligne
    dico["commId"] = int(commId)
    dico["src"] = int(src)
    dico["dst"] = int(dst)
    dico["taille_o"] = int(taille_o)
    dico["debut_ns"] = int(deb_ns)
    dico["fin_ns"] = int(fin_ns)
    dico["duree_ns"] = int(duree_ns)
    dico["tx_o"] = int(tx_o)
    dico["fini"] = True if fini=='YES' else False
    dico["groupe"] = groupe
    dico['debit_Mb/s']=dico['tx_o']*8000/dico["duree_ns"]
    return dico


def collecte_resultats_tcp(dos):
    #find run directory
    run_trouve=False
    for glob in os.listdir(dos):
        if glob.startswith('run_loaded') and os.path.isdir(os.path.join(dos, glob)):
            assert not run_trouve
            run_trouve = True
            run_glob= glob
    assert run_trouve
    # tx file
    tcpfic=os.path.join(dos, run_glob, "logs_ns3", "tcp_flows.csv")
    assert os.path.isfile(tcpfic)
    liste=[] 
    with open(tcpfic, 'r') as f:
        lecteur=csv.reader(f, delimiter=',')
        #94,804,847,3999250,2946944,16000000000,15997053056,3241620,NO_ONGOING,base
        #commId, src, dst, taille_o, deb_ns, fin_ns, duree_ns, tx_o, fini, groupe
        for ligne in lecteur:
            liste.append(TCPRes(ligne))
    stats={}
    stats['Total transmis (Mb)'] = sum(x["tx_o"]*8e-6 for x in liste)
    stats['Total upload (Mb)'] = sum(x["tx_o"]*8e-6 for x in liste if not x['commId']%2)
    stats['Ecart-type debits pairs (Mb/s)'] = np.std([x['debit_Mb/s'] for x in liste if x['commId']%2==0])
    stats['Ecart-type debits impairs (Mb/s)'] = np.std([x['debit_Mb/s'] for x in liste if x['commId']%2])
    return stats
