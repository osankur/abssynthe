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
        # print "<queries><query><formula>", self.query, "</formula></query></queries>"
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
        Loc_id = Loc_id + 1

    def set_invariant(self, invar):
        raise "not implemented"
    def dump(self):
        print "<location id=\"{0}\"><name>{1}</name>".format(self.id, self.name)
        if self.urgent:
            print "<urgent/>"
        if self.committed:
            print "<committed/>"
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
                si = map(lambda x: int(x), s.split(" "))
                assert(len(si) == 2)
                delays[latches[l]] = (si[0],si[1])
        log.DBG_MSG("Latch delays: " + str(delays))
        return delays

    def set_lit2formula(self, lit, s):
        self.lit_to_formula[lit] = s

    def clean_name(self, name):
        return name.replace("<", "_").replace(">","_");

    def lit2formula(self, lit):
        if lit in self.lit_to_formula:
            return self.lit_to_formula[lit]
        # get stripped lit
        stripped_lit = strip_lit(lit)
        is_neg = lit_is_negated(lit)
        (intput, latch, and_gate) = self.aig.get_lit_type(stripped_lit)
        # is it an input, latch, gate or constant
        if intput or latch:
            result = self.clean_name(self.aig.get_lit_name(stripped_lit))
        elif and_gate:
            result = ("({0} &amp; {1})".format(self.lit2formula(and_gate.rhs0),
                      self.lit2formula(and_gate.rhs1)))
        else:  # 0 literal, 1 literal and errors
            result = "false"
        # cache result
        self.lit_to_formula[stripped_lit] = result
        if is_neg:
            result = "!({0})".format(result)
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
        # clock name associated to given lit which is a latch
        clock_name = dict()
        # input name associated to given lit which is an input
        inputs = dict()
        # latch name associated to given lit which is a latch
        latches = dict()

        latch_locations = dict()
        nta = NTA()
        temp = Template("Circuit")
        nta.add_template(temp)
        nta.set_system("Process = Circuit();\nsystem Process;")
        decl = StringIO.StringIO()
        init = Location("Init", urgent=True,initial=True)
        for x in self.aig.iterate_latches():
            clock_name[x.lit] = "x_" + str(x.lit)
            print >> decl, "clock {0};".format(clock_name[x.lit])
        print >> decl, "clock t,T;"
        last_location = init
        input_list = list(chain(self.aig.iterate_uncontrollable_inputs(),self.aig.iterate_controllable_inputs()))
        for i in input_list:
            inputs[i.lit] = self.clean_name(self.aig.get_lit_name(i.lit))
            print >> decl, "bool {0};".format(inputs[i.lit])
            urgent = True
            if input_list[-1] == i:
                urgent = False
            loc_after_i = Location("JustSet"+inputs[i.lit], urgent=urgent)
            tr0 = Transition(last_location, loc_after_i, up="{0} := false".format(inputs[i.lit]))
            tr1 = Transition(last_location, loc_after_i, up="{0} := true".format(inputs[i.lit]))
            temp.add_transition(tr0)
            temp.add_transition(tr1)
            last_location = loc_after_i
            pass

        latch_list = list(self.aig.iterate_latches())
        latch_num = len(latch_list)
        next_funcs = self.get_next_funcs()

        for x in latch_list:
            latches[x.lit] = "L" + self.clean_name(self.aig.get_lit_name(x.lit))
            print >> decl, "bool {0};".format(latches[x.lit])
            latch_locations[x.lit] = Location("Updated"+ latches[x.lit])

            # Add the following transitions
            # up(l_i) ---- f(vec(l),I) = l_i, t=0, t:=0 ----> up(l_{i+1})
            # up(l_i) ---- f(vec(l),I) = 0 && l_i = 1, x_i >= D_i^1, l_i := 0, t:=0, x_i := 0 ----> up(l_{i+1})
            # up(l_i) ---- f(vec(l),I) = 1 && l_i = 0, x_i >= D_i^0, l_i := 1, t:=0, x_i := 0 ----> up(l_{i+1})
            g = "{0} == {1} &amp;&amp; t == 0".format(latches[x.lit], next_funcs[x.lit])
            tr = Transition(last_location, latch_locations[x.lit], guard=g, up="t:=0")
            temp.add_transition(tr)

            g = "{0} &amp;&amp; {0} != {1} &amp;&amp; {2} &gt;= {3}".format(latches[x.lit], next_funcs[x.lit], clock_name[x.lit], self.delays[x.lit][0])
            up="{0}:=0, {1} := {2}".format(clock_name[x.lit], latches[x.lit], next_funcs[x.lit])
            tr = Transition(last_location, latch_locations[x.lit], guard=g, up=up)
            temp.add_transition(tr)

            up="{0}:=0, {1} := {2}".format(clock_name[x.lit], latches[x.lit], next_funcs[x.lit])
            g = "!{0} &amp;&amp; {0} != {1} &amp;&amp; {2} &gt;= {3}".format(latches[x.lit], next_funcs[x.lit], clock_name[x.lit], self.delays[x.lit][1])
            tr = Transition(last_location, latch_locations[x.lit], guard=g, up=up)
            temp.add_transition(tr)

            last_location = latch_locations[x.lit]
            pass

        come_back= Transition(last_location, init, guard="T &lt;= {0}".format(str(K)), up="t:=0,T:=0")
        temp.add_transition(come_back)
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
