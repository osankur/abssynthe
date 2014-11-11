#!/usr/bin/python
import sys
import argparse
import pycudd
import aisy
from aiger_swig.aiger_wrap import *
from aiger_swig.aiger_wrap import aiger

# Compute the set of latches on which root_latch depends
# up to depth bound. A depth of bound means we stop exploring
# the tree right after we see bound number of latches on any given branch
def bounded_cone_of(root_latch, latches, bound=sys.maxint):
    cone = set([])
    wait = set([(bound,aisy.strip_lit(root_latch))])
    visited = set([])
    while len(wait) != 0:
        (bound,lit) = wait.pop()
        if (bound == 0):
            continue
        slit = aisy.strip_lit(lit)
        if ( slit in visited):
            continue;
        visited.add(slit)
        if (slit in latches):
            cone.add(slit)
        input_, latch_, and_ = aisy.get_lit_type(slit)
        if slit == 0:
            pass
        elif input_:
            pass
            # skip input for the moment
        elif latch_: 
            if (not (latch_.next in visited)):
                wait.add((bound-1,latch_.next))
        elif and_:
            if (not (and_.rhs0 in visited)):
                wait.add((bound,and_.rhs0))
            if (not (and_.rhs1 in visited)):
                wait.add((bound,and_.rhs1))
    #print "Just finished cone for latch ", root_latch, ":";
    #print visited;
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
        

def main(filename):
    aisy.parse_into_spec(filename)
    # but remove the fake error latch    
    latches = [l for l in aisy.iterate_latches_and_error() if l.name != 'fake_error_latch']
    #latches = [l for l in aisy.iterate_latches_and_error()]
    for l in latches:
        print (l.lit,l.name)
    latch_lits = map(lambda l: l.lit, latches)
    print "There are ", len(latch_lits), " latches";
#    for l in latches:
#        print l.lit, " n: ", l.next
#        print get_aiger_symbol(aisy.spec.latches,l)
    cones = []
    for lat in latches:
        cones.append( (lat.lit,bounded_cone_of(lat.lit, set(latch_lits))) )
    #print cones;
    cones = remove_subsumed(cones)
    for (lit,cone) in cones:
        percentage = "(%" + "{:.2f}".format(len(cone)/float(len(latches))) + " of latches)";
        print "Lit ", lit, "dependencies ", percentage;
        print cone;
    
    
if __name__ == '__main__':
    main(sys.argv[1])
