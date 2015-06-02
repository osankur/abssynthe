set term png size 600, 400 crop
set datafile separator ";"
set pointsize 2

set output "native_ca3_vars.png"
plot "< sort -n native_ca3.csv -k2 -t ';'" using ($2) title 'comp. 3' with lines, \
"< sort -n native_ca3_nose.csv -k2 -t ';'" using ($2) title 'comp. 3 nose' with lines,\

quit
