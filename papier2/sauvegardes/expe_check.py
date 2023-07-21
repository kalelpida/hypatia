import itertools
import sys, os, yaml, re
from multiprocessing.pool import ThreadPool

#Infos sur les expériences ayant réussi ou non
dossier=os.path.normpath(sys.argv[1])
assert os.path.isdir(dossier)


def simplival(cle, val, dicovals):
    for c, v in dicovals.items():
        if c.startswith(cle) and v==val:
            return c
    raise Exception(cle, val, "non trouvé dans", dicovals)

def lectExparams(fic, cles_variantes, dico_simplivals):
    with open(fic, 'r') as f:
        dic=yaml.load(f, Loader=yaml.Loader)
    return [simplival(x, dic[x], dico_simplivals) for x in cles_variantes] 

def lectExpResParams(glob, pack):
    cles_variantes, dico_simplivals = pack
    if not glob.is_dir() or not glob.name.startswith("svgde_"):
        return
    for ssglob in os.scandir(glob.path):
        if re.match("temp\\d+\.campagne\.yaml", ssglob.name):
            params=tuple(lectExparams(ssglob.path, cles_variantes, dico_simplivals))
        elif ssglob.name.startswith('run_loaded'):
            echec=glob.name
            ficfini=os.path.join(ssglob.path, "logs_ns3", "finished.txt")
            if os.path.isfile(ficfini):
                with open(ficfini, 'r') as f:
                    echec=False
    return [params, echec]

with open(os.path.join(dossier, "variations.txt"), 'r') as f:
    variations=eval(f.readline())

#paramètres de toutes les expériences
dico_vals={}
with open(os.path.join(dossier, "campagne.yaml"), 'r') as f:
    paramExpes=yaml.load(f, Loader=yaml.Loader)[os.path.basename(dossier)]
liste=[]
for cle in variations:
    infrliste=[]
    for i, a in enumerate(paramExpes[cle]):
        infrliste.append(f"{cle}--{i}")
        dico_vals[f"{cle}--{i}"]=a
    liste.append(infrliste)
ens_total=set(itertools.product(*liste))

p=ThreadPool(10)
results=p.starmap(lectExpResParams, itertools.zip_longest(os.scandir(dossier), [], fillvalue=(variations, dico_vals)))
exp_lues={a[0]: a[1] for a in results if a is not None}

print("\n\nExperiences non lancées: ", "\n".join([repr(x) for x in sorted(ens_total-set(exp_lues))]))

print("\n\nExpériences échouées")
for params, echec in exp_lues.items():
    if echec:
        print(os.path.basename(echec), params)

print("\n\nExplication des valeurs:")
for c,v in dico_vals.items():
    print(f"{c}:{v}")
        
