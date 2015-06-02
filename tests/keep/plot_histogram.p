#plot "< sort -n native_ca3.csv -k2 -t ';'" using ($2) title 'comp. 3' with lines, \
#"< sort -n native_ca3_nose.csv -k2 -t ';'" using ($2) title 'comp. 3 nose' with lines,\


set term png size 600, 400 crop
set datafile separator ";"
set pointsize 2
set output "hist_ca3.png"
set boxwidth 0.2 absolute
#set style fill solid 1.0 noborder
set key left top


Min = 0 # where binning starts
Max = 500 # where binning ends
n = 100 # the number of bins
width = (Max-Min)/n # binwidth; evaluates to 1.0
bin(x,offset) = width*(floor((x-Min)/width)+offset) + Min

plot 'native_big_ca3.csv' using (bin($2,0.25)):(1) smooth frequency with boxes title 'Native Comp. 3', \
'native_big_base.csv' using (bin($2,0.75)):(1) smooth frequency with boxes title 'Native Classic', \
'native_big_ca3.csv' using (bin($2,0.25)):(1) smooth cumulative with lines title 'Native Comp. 3 cum', \
'native_big_base.csv' using (bin($2,0.75)):(1) smooth cumulative with lines title 'Native Classic cum', \
#plot 'native_ca3.csv' using (rounded($2)):(1) smooth frequency with boxes

quit
