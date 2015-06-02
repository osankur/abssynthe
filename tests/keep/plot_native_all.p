set term png size 600, 400 crop
set datafile separator ";"
set pointsize 2

set key left top
set logscale y 10
set output "native_all.png"
plot "< sort -n native_base.csv -k2 -t ';'" using ($2) title 'Classic' with lines, \
"< sort -n native_ca1.csv -k2 -t ';'" using ($2) title 'Native ca.1' with lines,\
"< sort -n native_ca2.csv -k2 -t ';'" using ($2) title 'Native ca.2' with lines,\
"< sort -n native_ca3.csv -k2 -t ';'" using ($2) title 'Native ca.3' with lines,\

quit
