"""
Given an AIG file and a time configuration file TIME which contains a pair of integers for each latch. The TAWRITER class constructs a timed automaton which simulates this circuit with the following timing constraints.
For each latch, we are given the pair (delay[0],delay[1]). The circuit simulation can perform a new cycle if only if for each latch l:
- if l is about to change from 1 to 0, then at least delay[0] time units have passed since the value was changed to 1
- if l is about to change from 0 to 1, then at least delay[1] time units have passed since the value was changed to 0
If the value of l does not change, then there is no time constraint.

The present version computes an urgent model where each cycle is executed as soon as possible.
A deadlock is present iff there is a deadlock in the model (in the sense of Uppaal) or
location "dead" is reachable.

Latch names are obtained by replacing <, > characters by _ and by prefixing them by L
Input names are obtained ..................................
Clock names are obtained .................................. and by prefixing them by x_
"""
import sys
import argparse
import log
from itertools import chain
import StringIO

from aiger_swig.aiger_wrap import (
    get_aiger_symbol,
    aiger_init,
    aiger_open_and_read_from_file,
    aiger_is_input,
    aiger_is_latch,
    aiger_is_and,
    aiger_add_and,
    aiger_add_output,
    aiger_symbol,
    aiger_open_and_write_to_file,
    aiger_redefine_input_as_and,
    aiger_remove_outputs,
)
from aig import (
    AIG,
    strip_lit,
    lit_is_negated,
    symbol_lit,
    negate_lit
)

# This should be static to the Location class
Loc_id = 0

class NTA:
    def __init__(self):
        self.templates = []
        self.decl = ""
        self.inst = ""
        self.query = ""
        self.system= ""

    def set_instantiation(self, inst):
        self.inst = inst
    def set_query(self, query):
        self.query = query
    def set_system(self, system):
        self.system= system
    def add_template(self, t):
        self.templates.append(t)
    def set_declaration(self, decl):
        self.decl = decl

    def dump(self):
        print """<?xml version="1.0" encoding="utf-8"?><!DOCTYPE nta PUBLIC '-//Uppaal Team//DTD Flat System 1.1//EN' 'http://www.it.uu.se/research/group/darts/uppaal/flat-1_1.dtd'>"""
        print "<nta><declaration>", self.decl, "</declaration>"
        for temp in self.templates:
            temp.dump()
        print "<instantiation>{0}</instantiation>".format(self.inst)
        print "<system>{0}</system>".format(self.system)
        if self.query:
            print "<queries><query><formula>", self.query, "</formula></query></queries>"
        print "</nta>"

class Template:
    def __init__(self, name):
        self.name = name
        self.decl = ""
        self.locs = []
        self.trans = []

    def set_declaration(self, decl):
        self.decl = decl

    def add_location(self, loc):
        if not loc in self.locs:
            self.locs.append(loc)

    def add_transition(self, tr):
        if not tr in self.trans:
            self.trans.append(tr)
            self.add_location(tr.src)
            self.add_location(tr.tgt)

    def dump(self):
        print "<template><name>{0}</name>".format(self.name)
        if self.decl <> "":
            print "<declaration>{0}</declaration>".format(self.decl)
        for loc in self.locs:
            loc.dump()
        for loc in self.locs:
            if loc.initial:
                print "<init ref=\"{0}\"/>".format(loc.id)
        for tr in self.trans:
            tr.dump()
        print "</template>"

class Location:
    def __init__(self, name="", urgent=False, committed=False,initial=False):
        global Loc_id
        self.name = name
        self.id = "loc" + str(Loc_id)
        self.urgent = urgent
        self.committed = committed
        self.initial = initial
        self.invariant = None
        Loc_id = Loc_id + 1

    def set_invariant(self, invar):
        self.invariant = invar

    def dump(self):
        print "<location id=\"{0}\"><name>{1}</name>".format(self.id, self.name)
        if self.urgent:
            print "<urgent/>"
        if self.committed:
            print "<committed/>"
        if self.invariant:
            print "<label kind=\"invariant\">{0}</label>".format(self.invariant)
        print "</location>"

class Transition:
    def __init__(self, src, tgt, guard=None, sync=None, up=None):
        self.src = src
        self.tgt = tgt
        self.guard = guard
        self.sync = sync
        self.up = up
    def dump(self):
        print "<transition>\n<source ref=\"{0}\"/><target ref=\"{1}\"/>".format(self.src.id,self.tgt.id)
        if self.sync <> None:
            print "<label kind=\"synchronisation\">{0}</label>".format(self.sync)
        if self.up <> None:
            print "<label kind=\"assignment\">{0}</label>".format(self.up)
        if self.guard <> None:
            print "<label kind=\"guard\">{0}</label>".format(self.guard)
        print "</transition>"

class TAWRITER:
    def __init__(self, aiger_file_name, time_file_name):
        self.aig = AIG(aiger_file_name, False)
        self.lit_to_formula = dict()
        self._cached_transition = None
        self.delays = self._read_delays(time_file_name)


    def _read_delays(self, time_file_name):
        delays = dict()
        latches = [x.lit for x in self.aig.iterate_latches()]
        with open(time_file_name,'r') as fp:
            for l in range(len(latches)):
                s = fp.readline()
                if s <> "":
                #print "Doing line:<{0}>".format(s)
                #print s.split(" ")
                    si = map(lambda x: int(x), s.split(" "))
                    assert(len(si) == 2)
                    delays[latches[l]] = (si[0],si[1])
                else:
                    delays[latches[l]] = (0,0)
        log.DBG_MSG("Latch delays: " + str(delays))
        return delays

    def set_lit2formula(self, lit, s):
        self.lit_to_formula[lit] = s

    """ Name of stripped literal which must be an input or latch """
    def name_of(self, lit):
        assert(lit == strip_lit(lit))
        (intput, latch, and_gate) = self.aig.get_lit_type(lit)
        # is it an input, latch, gate or constant
        #print >> sys.stderr, "lit", lit, (input,latch,and_gate)
        if latch:
            return "L"+self.aig.get_lit_name(lit).replace("<", "_").replace(">", "_");
        elif input:
            # Boolean variables are encoded as 1-bit integers for now
            return "I"+self.aig.get_lit_name(lit).replace("<", "_").replace(">", "_");
        else:
            raise "And gates or constant inputs have no name"

    def lit2formula(self, lit):
        if lit in self.lit_to_formula:
            return self.lit_to_formula[lit]
        # get stripped lit
        stripped_lit = strip_lit(lit)
        is_neg = lit_is_negated(lit)
        (input, latch, and_gate) = self.aig.get_lit_type(stripped_lit)
        # is it an input, latch, gate or constant
        if input or latch:
            # Boolean variables are encoded as 1-bit integers for now
            result = "({0} == 1)".format(self.name_of(stripped_lit))
        elif and_gate:
            result = ("({0} &amp;&amp; {1})".format(self.lit2formula(and_gate.rhs0),
                      self.lit2formula(and_gate.rhs1)))
        else:  # 0 literal, 1 literal and errors
            result = "false" # this means false
        # cache result
        self.lit_to_formula[stripped_lit] = result
        if is_neg:
            if result == "false":
                result = "true"
            else:
                result = "!{0}".format(result)
            self.lit_to_formula[lit] = result
        return result

    def get_next_funcs(self):
        if self._cached_transition is not None:
            return self._cached_transition
        vec = dict()
        for x in self.aig.iterate_latches():
            vec[x.lit] = self.lit2formula(x.next)
        self._cached_transition = vec
        return vec

    """
    Given K, make timed automaton model that restricts each cycle to K time units.
    """
    def get_cycle_time_model(self, K):
        latch_locations = dict()
        # clock name associated to given lit which is a latch
        clock_name = dict()
        nta = NTA()
        temp = Template("Circuit")
        nta.add_template(temp)
        nta.set_system("Process = Circuit();\nsystem Process;")
        decl = StringIO.StringIO()
        init = Location("Init", urgent=True,initial=True)
        deadlock = Location("dead")
        # nta.set_query("E<>Process.dead")
        for x in self.aig.iterate_latches():
            clock_name[x.lit] = "x_" + str(x.lit)
            print >> decl, "clock {0};".format(clock_name[x.lit])
        print >> decl, "clock T;"
        last_location = init
        input_list = list(chain(self.aig.iterate_uncontrollable_inputs(),self.aig.iterate_controllable_inputs()))
        for i in input_list:
            print >> decl, "bool {0};".format(self.name_of(i.lit))
            loc_after_i = Location("JustSet"+self.name_of(i.lit), urgent=True)
            tr0 = Transition(last_location, loc_after_i, up="{0} := 0".format(self.name_of(i.lit)))
            tr1 = Transition(last_location, loc_after_i, up="{0} := 1".format(self.name_of(i.lit)))
            temp.add_transition(tr0)
            temp.add_transition(tr1)
            last_location = loc_after_i
            pass

        latch_list = list(self.aig.iterate_latches())
        latch_num = len(latch_list)

        next_funcs = self.get_next_funcs()

        for x in latch_list:
            print >> decl, "bool {0};".format(self.name_of(x.lit))
            latch_locations[x.lit] = Location("Updated"+ self.name_of(x.lit), urgent=True)

            # Basically, we add the following transitions but use intermediary states
            # with invariants so that all transitions are urgent
            # updated(l_{i-1},urg) ---- f(vec(l),I) = l_i ----> updated(l_{i+1})
            # updated(l_{i-1},urg) ---- f(vec(l),I) = 0 && l_i = 1, x_i >= D_i^1, l_i := 0, x_i := 0 ----> updated(l_{i},urg)
            # updated(l_{i-1},urg) ---- f(vec(l),I) = 0 && l_i = 1, x_i < D_i^1, l_i := 0, x_i := 0 ----> will_become1_nurg(l_{i})
            # symmetrically for when the new value is 1
            # will_become1_nurg(l_{i},invar:x_i<=D_i^1) ---- x_i >= D_i^0, l_i := 1, x_i := 0 ----> updated(l_{i}, urg)

            # if the value does not change:
            g = "{0} == {1}".format(self.name_of(x.lit), next_funcs[x.lit])
            tr = Transition(last_location, latch_locations[x.lit], guard=g)
            temp.add_transition(tr)

            # if it changes but the delay is already respected, move on directly
            g = "{0} &amp;&amp; {0} != {1} &amp;&amp; {2} &gt;= {3}".format(self.name_of(x.lit), next_funcs[x.lit], clock_name[x.lit], self.delays[x.lit][0])
            temp.add_transition(Transition(last_location, latch_locations[x.lit], guard=g))
            g = "!{0} &amp;&amp; {0} != {1} &amp;&amp; {2} &gt;= {3}".format(self.name_of(x.lit), next_funcs[x.lit], clock_name[x.lit], self.delays[x.lit][1])
            temp.add_transition(Transition(last_location, latch_locations[x.lit], guard=g))

            # if we have to wait to respect the delay go to specific wait state and wait precisely for the delay (matching invariant + guard)
            loc0 = Location(latch_locations[x.lit].name + "_becomes0")
            loc0.set_invariant("{0} &lt;= {1}".format(clock_name[x.lit], self.delays[x.lit][0]))
            loc1 = Location(latch_locations[x.lit].name + "_becomes1")
            loc1.set_invariant("{0} &lt;= {1}".format(clock_name[x.lit], self.delays[x.lit][1]))

            g = "{0} &amp;&amp; {0} != {1} &amp;&amp; {2} &lt; {3}".format(self.name_of(x.lit), next_funcs[x.lit], clock_name[x.lit], self.delays[x.lit][0])
            tr = Transition(last_location, loc0, guard=g)
            temp.add_transition(tr)

            up="{0}:=0, {1} := {2}".format(clock_name[x.lit], self.name_of(x.lit), next_funcs[x.lit])
            g = "{0} &gt;= {1}".format(clock_name[x.lit], self.delays[x.lit][0])
            tr = Transition(loc0, latch_locations[x.lit], guard=g, up=up)
            temp.add_transition(tr)

            g = "!{0} &amp;&amp; {0} != {1} &amp;&amp; {2} &lt; {3}".format(self.name_of(x.lit), next_funcs[x.lit], clock_name[x.lit], self.delays[x.lit][1])
            tr = Transition(last_location, loc1, guard=g)
            temp.add_transition(tr)

            up = "{0}:=0, {1} := {2}".format(clock_name[x.lit], self.name_of(x.lit), next_funcs[x.lit])
            g = "{0} &gt;= {1}".format(clock_name[x.lit], self.delays[x.lit][1])
            tr = Transition(loc1, latch_locations[x.lit], guard=g, up=up)
            temp.add_transition(tr)

            last_location = latch_locations[x.lit]
            pass
        go_deadlock=Transition(last_location, deadlock, guard="T &gt;{0}".format(str(K)))
        come_back= Transition(last_location, init, guard="T &lt;= {0}".format(str(K)), up="T:=0")
        temp.add_transition(come_back)
        temp.add_transition(go_deadlock)
        last_location = init
        nta.set_declaration(decl.getvalue())
        nta.dump()

    def test(self):
        vec = self.get_next_funcs();
        for x in vec:
            print >> sys.stderr, "NEXT(",x,")"
            print >> sys.stderr, vec[x]
            print >> sys.stderr, ""

def main():
    parser = argparse.ArgumentParser(description="AIG Format Based Synth")
    parser.add_argument("spec", metavar="spec", type=str,
                        help="input specification in extended AIGER format")
    parser.add_argument("time", metavar="time", type=str,
                        help="time specifications")
    parser.add_argument("-v", "--verbose_level", dest="verbose_level",
                        default="", required=False,
                        help="Verbose level = (D)ebug, (W)arnings, " +
                             "(L)og messages, (B)DD dot dumps")
    parser.add_argument("-o", "--out_file", dest="out_file", type=str,
                        required=False, default=None,
                        help=("Output file path. If file extension = .aig, " +
                              "binary output format will be used, if " +
                              "file extension = .aag, ASCII output will be " +
                              "used. The argument is ignored if the spec is " +
                              "not realizable."))
    args = parser.parse_args()
    log.parse_verbose_level(args.verbose_level)
    # realizability / synthesis
    tawriter = TAWRITER(args.spec, args.time)
    tawriter.test();
    tawriter.get_cycle_time_model(50)

if __name__ == "__main__":
    main()
# add urgency
