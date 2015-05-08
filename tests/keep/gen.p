set term png size 600, 400 crop
set datafile separator ";"
set pointsize 2

set logscale y 10
set output "gen.png"
plot "< sort -n classic_gen.csv -k2 -t ';'" using ($2) title 'classic' with lines,\
"< sort -n ca2_gen.csv -k2 -t ';'" using ($2) title 'comp. 2' with lines, \

quit
