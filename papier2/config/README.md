# Configuration d'une Campagne

Une campagne est un ensemble d'expériences décrites par un sous-dictionnaire dans `campagne.yaml`. 
Parmi ces sous-dictionnaires, on trouve:

+ des actions, c'est à dire définition des commodité, création des fichiers de route, simulation en elle-même. C'est ici que sont déterminées toutes les actions à effectuer. Les actions ne sont pas forcément effectuées lorsqu'elles sont inutiles (lire paper3.py directement)
+ info-sauvegarde permet de définit quels fichiers sauvegarder pour chaque expérience. Les 'sources' seront copiées dans le dossier d'expérience (expedir), lui-même sauvegardé dans le dossier de campagne (campagnedir)
+ des configurations de campagne. Actuellement, hormis les deux mots-clef précédents, tous les autres sous-dictionnaires Yaml définissent une campagne.

## La campagne

La campagne détermine tous les aspect simulation. Chaque clé contient une liste de valeur. Toutes les valeurs de toutes les listes seront simulées. Ainsi, les paramètres suivants
```
exemple-campagne: #nom de la campagne
  graine: [0, 1]
  duree: [ 4, 6 ] #en s
```

Lanceront 4 expériences. Les expériences sont lancées une à une. La première aura pour configuration 
```
graine: 0
duree: 4
```

qui sera notée dans le fichier `courante.yaml`

## La topologie

Pour conserver un fichier de paramètres plus concis, il semblait préférable de définir la topologie autre part. Alors que le fichier campagne a pour but de rendre les paramètres faciles à modifier, les fichiers de topologie doivent permettrent de décrire de façon la plus claire possible une architecture réseau. Initialement ils ne servaient qu'à décrire la constellation, pour cette raison ils ont un nom de constellation et correspondent à la clé 'constellation' dans `campagne.yaml`.

La topologie décrit successivement 
1. La constellation
2. Les autres objets, jusqu'à présent statiques au sol
3. Les liens entre ces objets

Les noms des objets sont en minuscules. Avant de revenir aux groupes d'objets, voyons l'architecture

### Syntaxe des liens - LINKS

Un liant est défini de la façon suivante:
   [nom-du-liant, dico-propriétés-des-interfaces, dico-propriétés-des-liens ]

#### Le liant

Le liant définit les liens entre des interfaces présentes sur différents objets. Il y a deux méthode pour relier plusieurs interfaces: 
- Soit il y a un unique canal pour toutes les interfaces. En interne, la topologie peut être représentée comme un bus. Le canal est alors le commis qui transporte les message d'une interface à l'autre. Le débit sortant d'une interface est alors partagées à toutes les destinations depuis lesquelles elle émet à travers le canal.
- Soit il y a un canal par paire. En interne, la topologie est plutôt une étoile, l'objet a plusieurs interfaces et lorsqu'une interface émet dans un canal, l'information parvient à l'interface située à l'autre bout.


Jusqu'ici 4 liants sont définis:
1. isl "lien inter-satellite" relie un satellite à chacun de ses voisins par un canal simple. Le délai est basé sur la distance géométrique entre les deux satellites, réévaluée à chaque émission de paquet. Il doit être utilisé sur le seul groupe d'objet "satellite", pour permettre de les lier entre eux par une maille en "+". Il 
2. gsl "lien sol-satellite" définit un canal entre des objets divers. Tous peuvent transmettre à tous, le délai dépend de la distance qui sera évaluée à l'émission du paquet.
3. tl "lien terrestre" définit un canal entre 2 ordinateurs.
4. pyl "lien pyramidal" prend en entrée deux groupes. Les objets du premier groupe sont reliés à des objets du second groupe par autant d'interfaces que nécessaire. Les objets sont reliés deux à deux par un canal spécifique, dont le délai est défini initialement par le paramètre Délai (par défaut 0) plus le délai dû à la distance orthodromique entre les deux objets.

#### Propriétés du liant
Le champs "dico-propriétés-des-liens" contient des paramètres supplémentaires utilisés pour définir le liant ou des paramètres communs à toutes les interfaces. Par exemple le Délai et son estimation "estimDelai" utilisée pour régler la taille de la file d'attente (buffer) de l'interface. Il est possible d'ajouter une pénalité "penalite_s" pour pénaliser des liens lors du calcul des routes. "limiteDist" sert dans le cas des liants "gsl" et "isl" à déterminer si deux objets peuvent communiquer directement ou non. Les tables de routages seront calculées en fonction.


#### Propriétés des interfaces
Le "dico-propriétés-des-interfaces" est un dictionnaire dont les clés sont les groupes d'objets à lier, tandis que les valeurs sont les paramètres des interfaces. 


Dans ns3, les interfaces sont crées l'une après l'autre, en commençant par la loopback (lo). L'ordre de définition des interfaces, c'est à dire leur numéro, sera utilisé pour définir les tables de routages lues par ns-3 aux différents pas de temps pendant la simulation.


Le dico propriétés est constitué des paramètres des différents objets.
En clé principale, le nom des objets
Puis: 
    Attribut : Unité_ns3~Valeurns3
Pour définir et ajouter un contrôleur de traffic, spécifier
"QueueDisc" : ns3::classe_de_traffic_control
Attribut : Unité_ns3 Valeurns3 (avec un espace entre le type et la valeur)
Il est possible de chainer une QDisc classless sur une classfull, en ajoutant le préfixe Child. 

La taille du buffer d'émission d'un netdevice est masqué ici. Il s'agit d'une DropTailQueue, dont la taille est mise au produit DataRate estimDelai. Lorsqu'il y a une QueueDisc, ce buffer a la taille minimale de 2kB.

Les paramètres des objets sont ceux d'un Netdevice, notamment
'DataRate': "DataRate~[debit][unité]" //débit du netdevice

Les paramètres non typés ne sont lus que par python, par exemple
'maxSatellites' utilisé dans les gsl limite le nombre de satellites avec lesquels communiquer (dans la limite de ceux visibles avec minElevation)


### Les groupes d'objets

Le groupe "satellite" est spécial, il a ses paramètres propres, ceux de la constellation.

Tous les autres sont des groupes d'objets fixes, dont les positions sont  les `nombre` premières lignes du fichier "papier2/satellite_networks_state/input_data/`positions`{.txt|.csv}"

D'autres attributs peuvent y être définis, tels l'élévation minimale dans le cas du liant 'gsl'.

### Passage de paramètres

Pour tester différents paramètres de topologie, il est conseillé de passer par le fichier `campagne.yaml`. Lorsqu'une simulation est lancée, le fichier `courante.yaml` est écrit. Il est possible de récupérer des valeurs de ce fichier depuis la configuration de topologie en appelant 
`$config/la-variable-désirée`. 

L'exemple ci-dessous illustre le passage de paramètres

courante.yaml:
```
nb-UEs-sol: 3
debit-if-gsl: { "ue": 1, "gateway": 3}
trafficControl: {"QueueDisc": "ns3::DropTailQueue", "MaxSize": "QueueSize 100p"}
```

temp.constellation avant remplacement:
```
ue:
  positions: os_1villes_kuiper630
  nombre: $config/nb-UEs-sol
LINKS:
    - ["gsl", { "gateway": { 'DataRate': $config/debit-if-gsl/gateway }, "ue": { 'DataRate': "DataRate~$config/debit-if-gsl/ue/Mbps", $config/trafficControl }}, {"limiteDist": True }]
```

temp.constellation après remplacement:
```
ue:
  positions: os_1villes_kuiper630
  nombre: 3
LINKS:
    - ["gsl", { "gateway": { 'DataRate': 3 }, "ue": { 'DataRate': "DataRate~1Mbps", "QueueDisc": "ns3::DropTailQueue", "MaxSize": "QueueSize 100p" }}, {"limiteDist": True }]
```