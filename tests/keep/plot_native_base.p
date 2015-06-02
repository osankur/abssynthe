set term png size 600, 400 crop
set datafile separator ";"
set pointsize 2

set key left top
set logscale y 10
set output "native_big_ca3.png"
plot "< sort -n native_big_base.csv -k2 -t ';'" using ($2) title 'Native base' with lines,\
"< sort -n native_big_ca3.csv -k2 -t ';'" using ($2) title 'Native ca.3 b4' with lines,\

quit
