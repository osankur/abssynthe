set term png size 600, 400 crop
set datafile separator ";"
set pointsize 2

set style func linespoints
set style line 1 lc rgb 'green' lt 2 lw 1 pt 1 pi -1 ps 0.5
set style line 2 lc rgb 'red' lt 1 lw 2 pt 2 pi -1 ps 0.5
set style line 3 lc rgb 'blue' lt 3 lw 2 pt 2 pi -1 ps 0.5
set style line 4 lc rgb 'purple' lt 4 lw 2 pt 2 pi -1 ps 0.5
set style line 5 lc rgb 'magenta' lt 5 lw 2 pt 2 pi -1 ps 0.5

set logscale y 10
set output "more30.png"
plot "< sort -n more30.csv -k2 -t ';'" using ($2) title 'classic' with linespoints ls 1,\
"< sort -n more30.csv -k3 -t ';'" using ($3) title 'comp. 1' with linespoints ls 2,\
"< sort -n more30.csv -k4 -t ';'" using ($4) title 'comp. 2' with linespoints ls 3,\
"< sort -n more30.csv -k5 -t ';'" using ($5) title 'comp. 3' with linespoints ls 4,\
"< sort -n more30.csv -k6 -t ';'" using ($6) title 'minimum' with linespoints ls 5

set logscale y 10
set output "load.png"
plot "< sort -n load.csv -k2 -t ';'" using ($2) title 'classic' with linespoints ls 1,\
"< sort -n load.csv -k3 -t ';'" using ($3) title 'comp. 1' with linespoints ls 2,\
"< sort -n load.csv -k4 -t ';'" using ($4) title 'comp. 2' with linespoints ls 3,\
"< sort -n load.csv -k5 -t ';'" using ($5) title 'comp. 3' with linespoints ls 4,\
"< sort -n load.csv -k6 -t ';'" using ($6) title 'minimum' with linespoints ls 5

set logscale y 10
set output "genbuf.png"
plot "< sort -n genbuf.csv -k2 -t ';'" using ($2) title 'classic' with linespoints ls 1,\
"< sort -n genbuf.csv -k3 -t ';'" using ($3) title 'comp. 1' with linespoints ls 2,\
"< sort -n genbuf.csv -k4 -t ';'" using ($4) title 'comp. 2' with linespoints ls 3,\
"< sort -n genbuf.csv -k5 -t ';'" using ($5) title 'comp. 3' with linespoints ls 4,\
"< sort -n genbuf.csv -k6 -t ';'" using ($6) title 'minimum' with linespoints ls 5

set logscale y 10
set output "amba.png"
plot "< sort -n amba.csv -k2 -t ';'" using ($2) title 'classic' with linespoints ls 1,\
"< sort -n amba.csv -k3 -t ';'" using ($3) title 'comp. 1' with linespoints ls 2,\
"< sort -n amba.csv -k4 -t ';'" using ($4) title 'comp. 2' with linespoints ls 3,\
"< sort -n amba.csv -k5 -t ';'" using ($5) title 'comp. 3' with linespoints ls 4,\
"< sort -n amba.csv -k6 -t ';'" using ($6) title 'minimum' with linespoints ls 5

quit
