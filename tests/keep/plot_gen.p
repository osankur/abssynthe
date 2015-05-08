set term png size 600, 400 crop
set datafile separator ";"
set pointsize 2
set key left top
set logscale y 10
set output "gen.png"
plot "< sort -n classic_gen.csv -k2 -t ';'" using ($2) title 'classic' with lines, \
"< sort -n ca1_gen.csv -k2 -t ';'" using ($2) title 'comp. 1' with lines,\
"< sort -n ca2_gen.csv -k2 -t ';'" using ($2) title 'comp. 2' with lines,\
"< sort -n ca3_gen.csv -k2 -t ';'" using ($2) title 'comp. 3' with lines,\
"min_all_gen.csv" using ($2) title 'minimum' with lines

quit
