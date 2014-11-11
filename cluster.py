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
    cones = list(cones)
    for i in range(len(cones)):
        (lit,cone) = cones[i];
        if (cone == None):
            continue;
        for (litb,coneb) in cones:
            if (coneb != None and cone.issubset(coneb) and not(cone is coneb) ):
                cones[i] = (lit,None)
    cones = [(lit,cone) for (lit,cone) in cones if cone != None]
    return cones

def print_clusters(cones, latches):        
    for (lit,cone) in cones:
        percentage = "(%" + "{:.2f}".format(100 * len(cone)/float(len(latches))) + " of latches)";
        print >> stderr, "Lit ", lit, "dependencies ", percentage;
        print >> stderr, cone;

def to_lit(latch_list):
    return map(lambda lat: lat.lit, latch_list)

def get_clusters(include_err_latch = False, depth=sys.maxint):
    latches = [l for l in aig.iterate_latches() if l.name != 'fake_error_latch' or include_err_latch]
    clusters = [[],[]]
    for i in range(len(latches)):
        clusters[i % 2].append(latches[i])
    print "ARBITRARILY DIVIDING LATCHES INTO TWO"
    return map(lambda cl: set(cl),clusters)
    for l in latches:
        print >> stderr, (l.lit,l.name)
    latch_lits = map(lambda l: l.lit, latches)
    if cluster_debug:
        print >> stderr, "There are ", len(latch_lits), " latches";
    cones = []
    for lat in latches:
        cones.append( (lat.lit,bounded_cone_of(lat.lit, set(latch_lits), depth)) )
    cones = remove_subsumed(cones)
    if cluster_debug:
        print "Initial set of cones\n"
        print_clusters(cones, latches)
    cones = map(lambda (lit,cone): cone, cones)
    cones = map(lambda clust: map(lambda lit: aig.get_lit_type(lit)[1], clust), cones)
    cones = sorted(cones,cmp=lambda l1,l2: cmp(len(l1),len(l2)))
    # If error latch is there, then remove all singletons
    if (include_err_latch and depth == sys.maxint):
        while(len(cones)> 0 and len(cones[0])==1):
            cones.pop(0)
    print "Removed singletons, we get:"
    for cone in cones:
        print map(lambda lat: lat.lit, cone)
    print "Now merging"
    while( len(cones) > 2):
        a = cones.pop(0)
        b = cones.pop(0)
        #print "Got two sets: " + str(to_lit(a)) + " and " + str(to_lit(b))
        cones.append(list(set(a).union(set(b))))
        cones = sorted(cones,cmp=lambda l1,l2: cmp(len(l1),len(l2)))
        #for cone in cones:
        #    print map(lambda lat: lat.lit, cone)
        #print "--"
    #print "After sorting"
    for cone in cones:
        print map(lambda lat: lat.lit, cone)
    return cones
#    if cluster_debug :
#        for cl in clusters:
#            percentage = "(%" + "{:.2f}".format(len(cone)/float(len(latches))) + " of latches)";
#            print >> stderr, "Lit ", lit, "dependencies ", percentage;
#            print >> stderr, map(lambda lat: lat.lit, cl);

    
if __name__ == '__main__':
    if (len(sys.argv) < 2):
        print "Not enough arguments"
        exit(-1)
    include_err_latch = False
    if (len(sys.argv) > 2):
        if (sys.argv[2] == "-e"):
            include_err_latch = True;
            print "setting err latch to true"
    aig.parse_into_spec(sys.argv[1])
    aig.introduce_error_latch()
    get_clusters(include_err_latch,1)
