set term png size 600, 400 crop
set datafile separator ";"
set pointsize 2

set output "ca2_switch.png"
plot "< sort -n ca2_gen.csv -k2 -t ';'" using ($2) title 'comp. 2' with lines, \
"< sort -n ../ca2_switch5000.csv -k2 -t ';'" using ($2) title 'comp. 2 switch' with lines,\

quit
