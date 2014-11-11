#!/usr/bin/python
import sys
from sys import stderr
import argparse
import pycudd
import aig
from aiger_swig.aiger_wrap import *
from aiger_swig.aiger_wrap import aiger

cluster_debug = True

# Compute the set of latches on which root_latch depends
# up to depth bound. A depth of bound means we stop exploring
# the tree right after we see bound number of latches on any given branch
def bounded_cone_of(root_latch, latches, bound=sys.maxint):
    cone = set([])
    wait = set([(bound,aig.strip_lit(root_latch))])
    visited = set([])
    while len(wait) != 0:
        (bound,lit) = wait.pop()
        if (bound == 0):
            continue
        slit = aig.strip_lit(lit)
        if ( slit in visited):
            continue;
        visited.add(slit)
        if (slit in latches):
            cone.add(slit)
        input_, latch_, and_ = aig.get_lit_type(slit)
        if slit == 0:
            pass
        elif input_:
            pass
        elif latch_: 
            if (not (latch_.next in visited)):
                wait.add((bound-1,latch_.next))
        elif and_:
            if (not (and_.rhs0 in visited)):
                wait.add((bound,and_.rhs0))
            if (not (and_.rhs1 in visited)):
                wait.add((bound,and_.rhs1))
    return cone
        
def remove_subsumed(cones):
    cones = [a for a in cones]
    for i in range(len(cones)):
        (lit,cone) = cones[i];
        if (cone == None):
            continue;
        for (litb,coneb) in cones:
            if (coneb != None and cone.issubset(coneb) and cone != coneb ):
                cones[i] = (lit,None)
    cones = [(lit,cone) for (lit,cone) in cones if cone != None]
    return cones
        

def get_clusters(include_err_latch = False):
    latches = [l for l in aig.iterate_latches() if l.name != 'fake_error_latch' or include_err_latch]
    for l in latches:
        print >> stderr, (l.lit,l.name)
    latch_lits = map(lambda l: l.lit, latches)
    if cluster_debug:
        print >> stderr, "There are ", len(latch_lits), " latches";
    cones = []
    for lat in latches:
        cones.append( (lat.lit,bounded_cone_of(lat.lit, set(latch_lits))) )
    cones = remove_subsumed(cones)
    if cluster_debug:
        for (lit,cone) in cones:
            percentage = "(%" + "{:.2f}".format(100 * len(cone)/float(len(latches))) + " of latches)";
            print >> stderr, "Lit ", lit, "dependencies ", percentage;
            print >> stderr, cone;
    cone_list = map(lambda (lit,cone): cone, cones)
    clusters = map(lambda clust: set(map(lambda lit: aig.get_lit_type(lit)[1], clust)), cone_list)
#    if cluster_debug :
#        for cl in clusters:
#            percentage = "(%" + "{:.2f}".format(len(cone)/float(len(latches))) + " of latches)";
#            print >> stderr, "Lit ", lit, "dependencies ", percentage;
#            print >> stderr, map(lambda lat: lat.lit, cl);


    
    
if __name__ == '__main__':
    if (len(sys.argv) < 2):
        print "Not enough arguments"
        exit(-1)
    aig.parse_into_spec(sys.argv[1])
    get_clusters()
