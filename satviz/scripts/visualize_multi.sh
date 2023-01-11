fics=$(find ../../papier2/sauvegardes/reunion0601 -type f -name "isl_utilization.csv")
#fics=$(find ../../papier2/sauvegardes/svgde_global/svgde*sanslien*_2 -type f -regex ".*[21]0?_Mbps.*/isl_utilization.csv")

for fic in $fics; do 
	python visualize_utilization.py $fic
done
