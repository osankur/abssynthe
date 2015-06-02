set term png size 600, 400 crop
set datafile separator ";"
set pointsize 2
set key left top
set logscale y 10
set output "ca1_native.png"
plot "ca1_gen.csv" using ($2) title 'comp. 1' with lines,\
"< sort -n native_ca1.csv -k2 -t ';'" using ($2) title 'native ca 1' with lines

quit
