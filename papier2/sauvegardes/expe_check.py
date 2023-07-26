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
                    echec= echec if f.readline().startswith("No") else False
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

with ThreadPool(10) as p:
    results=p.starmap(lectExpResParams, itertools.zip_longest(os.scandir(dossier), [], fillvalue=(variations, dico_vals)))
results=list(filter(lambda item: item is not None, results))
"experiences lancées"
lancees=set([x[0] for x in results])
nonlancees=ens_total-lancees
if len(nonlancees)<len(lancees):
    print("\n\nExperiences non lancées: ", "\n".join([repr(x) for x in sorted(nonlancees)]),"\n:Experiences non lancées")
else:
    print("\n\nExperiences lancées: ", "\n".join([repr(x) for x in sorted(lancees)]), "\n:Experiences lancées")

print("\n\nExpériences échouées:")
aumoinsunechec=False
for params, echec in results:
    if echec:
        print(os.path.basename(echec), params)
        aumoinsunechec=True
if not aumoinsunechec:
    print("pas d'échec relevé")

supprimes=[]
if aumoinsunechec:
    poubelle=f"{dossier}_echouees"
    rep=input(f"Déplacer les expériences vers {poubelle} ? (o/N)")
    if rep.lower()[0]=='o':
        os.makedirs(poubelle, exist_ok=True)
        for _, echec in results:
            if echec:
                print(os.path.join(dossier, echec), '  ---->>  ', os.path.join(poubelle, echec))
                os.replace(os.path.join(dossier, echec), os.path.join(poubelle, echec))
                supprimes.append(echec)
        print("Déplacement terminé")

print("\n\nduplicats:")
expedic={}
duplicats=False
for x, dos in results:
    if dos in supprimes:
        continue
    if x in expedic:
        expedic[x].append(dos)
        duplicats=True
    else:
        expedic[x]=[dos]
if not duplicats:
    print("aucun relevé qui n'ait pas été supprimé")
else:
    poubelle=f"{dossier}_duplicats"
    rep=input(f"Déplacer les duplicats vers {poubelle} ? (o/N)")
    deplace=(rep.lower()[0]=='o')
    if deplace:
        os.makedirs(poubelle, exist_ok=True)
    for params, doss in expedic.items():
        if len(doss)>1:
            print(params, doss)
            if deplace:
                for dup in doss[1:]:
                    print(os.path.join(dossier, dup), '  ---->>  ', os.path.join(poubelle, dup))
                    os.replace(os.path.join(dossier, dup), os.path.join(poubelle, dup))


print("\n\nExplication des valeurs:")
for c,v in dico_vals.items():
    print(f"{c}:{v}")
        
