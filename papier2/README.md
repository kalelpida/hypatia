# Ce qui a changé

Ce dossier a été remanié de Hypatia pour lancer des simulations. Les appels à des lignes de commande bash le rendait facile à distribuer, tout cela a été modifié pour le rendre plus simple à déboguer. Au lieu de distribuer le code, on préférera lancer des expériences différentes sur des machines différentes.	

# Résumé de hypatia

+ hypatia/ns3-sat-sim contient le simulateur ns3 + des modules spécifiques dans contrib
	+ le fichier principal est hypatia/ns3+sat+sim/simulator/scratch/main_satnet/main_satnet.cc
+ hypatia/papier2 contient les scripts de configuration de la topologie et de ns3, ainsi que les résultats lorsque le script a été correctement executé
+ hypatia/satgenpy contient la génération des constellations, du routage, et des outils d'analyse.
+ hypatia/satviz permet de générer les visualisations 3D avec Cesium
	+ À noter pour césium: il faut créer un compte sur https://cesium.com/ion/signup/tokens pour récupérer un token
	+  copier le token dans hypatia/satviz/static_html/top.html
	+  modifier les fichiers à analyser des scripts de hypatia/satviz/scripts et les exécuter
	+  ouvrir les fichiers générés dans hypatia/satviz/viz_output.
		+  dans certains cas, Firefox refuse par défaut de télécharger le javascript permettant de visualiser. Solution temporaire: ouvrir la console dans "outils de développement" : une erreur est levée sur le fichier https://cesiumjs.org/releases/1.57/Build/Cesium/Cesium.js Il suffit d'accepter de le télécharger malgré les risques de sécurité (partage du jeton cesium)


# Démarrage rapide

étapes:
 + Installer hypatia comme prévu avec `hypatia_install_dependencies.sh` et `hypatia_build.sh` à la racine du projet. 
 + Les calculs de MultiCommodity Network Flow ont besoin de Gurobi. Gurobi propose des licenses académiques. Gurobipy ne suffit pas, il faut télécharger la librairie Gurobi Optimizer, et activer les fonctionnalités avec une license Gurobi.
 + configurer les expériences à mener dans `config/campagne.yaml`.
	+ Ce fichier décrit l'ensemble des expérience à mener. Le script d'exécution sélectionne une valeur pour chaque clé et génère un fichier `config/courante.yaml` qui contient les paramètres choisis pour la simulation.
	+ ce fichier décrit aussi les fichiers qui seront sauvegardés à la fin.
 + Exécuter le script d'exécution (`paper3.py`) pour lancer les simulations une à une, et sauvegarder chaque campagne dans un dossier du même nom.
 + récupérer les résultats
	+ Après chaque expérience, si toutes les `actions` de la campagne ont été activées, on retrouve
		+ dans satgenpy_analysis/data les routes calculées et l'estimation des RTT par networkx
		+ dans ns3_experiments/traffic_matrix_load/runs les traces réseau
	+ En fonction de la configuration les `sources` de l'expérience sont copiées dans un dossier dans sauvegarde/nom_campagne
+ analyser les résultats
	+ cela peut se faire avec les scripts `sauvegardes/étudesX.py` qui permettent de visualiser les performances des flux et autres (progressivement déprécié)
	+ pour des visuels césium, se reporter à `../satviz/` 


En fonction des paramètres de la campagne, les fichiers enregistrés peuvent varier. En parcourant les dossiers, on peut retrouver des paramètre de la simulation:
 - campagne.yaml : détermine l'ensemble des simulations à lancer
 - courante.yaml : les paramètres de la simulation du dossier présent. Correspond à une simulation parmi celles demandées dans 'campagne.yaml'
 - ground_stations.txt : les stations 5G puis utilisateurs, dont le format est 'id, nom, latitude(deg), longitude(deg), élévation (m), position XYZ(m, référentiel terrestre lié au centre de la Terre), type'
 Des fichiers intermédiaires:
 - commodites.temp, forme pythonesque des commodités, valable lorsque udp est seul
 - tcp_flow_schedule.csv, format: 'id commodité, src, dst, taille du fichier à uploader (o), instant démarrage (ns)
 - udp_burst_schedule.csv, format : 'id commodité, src, dst, débit (Mb/s), instant de début (ns), fin (ns)
  - config_ns3.properties: décrit les paramètres principaux de ns3
 Ainsi que les résultats:
 - des fichiers de statistiques globales sur les flux : 'udp_bursts_incoming', 'udp_bursts_outgoing', 'tcp_flows'
 - des fichiers de contrôle de congestion pour la X-ième commodité: tcp_flow_X_{cwnd|progress|rtt}
 - des fichier contenant les métadonnées de tous les paquets:
   * link.rx contient tout les paquets reçus par tous les nœuds. Il contient notamment les champs 'instant (ns), src, id commodité, numero de séquence (si UDP), offset (si TCP), taille données (o), estUnFluxTCP, estRetour, information
   * link.drops contient tous les paquets perdus. Il contient notamment les champs instant (ns), nœud, id commodité, numero de séquence (si UDP), offset (si TCP), taille données (o), estUnFluxTCP, estRetour, cause de la perte
   * link.tx contient tous les paquets transmis. Il contient notamment les champs instant (ns), src, dst, id commodité, numero de séquence (si UDP), offset (si TCP), taille données (o), estUnFluxTCP, estRetour, info'

# Configuration d'une campagne

Voir config/README.md


