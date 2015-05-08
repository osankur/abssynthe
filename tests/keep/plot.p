set term png size 600, 400 crop
set datafile separator ";"
set pointsize 2

set logscale y 10
set output "ca2_pij.png"
plot "< sort -n ca2_nopij.csv -k2 -t ';'" using ($2) title 'comp. 2' with lines, \
"< sort -n ca2_pij.csv -k2 -t ';'" using ($2) title 'comp. 2 pij' with lines,\
"< sort -n ca2_pij_norestr.csv -k2 -t ';'" using ($2) title 'comp. 2 pij no restr' with lines,\

quit
