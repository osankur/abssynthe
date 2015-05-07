"""
Copyright (c) 2014, Guillermo A. Perez, Universite Libre de Bruxelles

This file is part of the AbsSynthe tool.

AbsSynthe is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

AbsSynthe is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with AbsSynthe.  If not, see <http://www.gnu.org/licenses/>.


Guillermo A. Perez
Universite Libre de Bruxelles
gperezme@ulb.ac.be
"""

from itertools import imap

import log
from cudd_bdd import BDD
from aig import (
    symbol_lit,
)
from utils import funcomp, fixpoint
from algos import (
    BackwardGame,
    ForwardGame,
)
import sys

class ConcGame(BackwardGame):
    def __init__(self, aig, use_trans=False, opt_type=1):
        self.use_trans = use_trans
        self.aig = aig
        self.short_error = None
        self.opt_type = opt_type
        self.coreachable_states = None
        if (self.opt_type == 3):
            # Here the usual upre fixpoint is no more correct
            # However we will intersect coreachables() after each
            # iteration of upre, which then becomes exact
            # self.aig.restrict_latch_next_funs(self.coreachables())
            cor = self.coreachables()
            latdep = self.aig.get_bdd_latch_deps(cor)
            log.LOG_MSG("Coreachables depend on " + str(len(latdep)) + " latches")
            latches_and_restricted_funs = []
            orig_total_size = 0
            rest_total_size = 0
            for l in self.aig.iterate_latches():
                if l != self.aig.error_fake_latch:
                    restr_fun = self.aig.lit2bdd(l.next).restrict(cor)
                    latches_and_restricted_funs.append( (l, restr_fun) )
                    orig_total_size = orig_total_size + self.aig.lit2bdd(l.next).dag_size()
                    rest_total_size = rest_total_size + restr_fun.dag_size()
            if (rest_total_size < orig_total_size):
                # We set the transition functions to the restricted ones
                print "GOOD"
                sys.exit(-1)
                log.LOG_MSG("Restricting next funs by coreachables()")
                log.LOG_MSG("\t Total dag size of next funs were " +
                        str(orig_total_size) + " now " + str(rest_total_size))
                for (l,f) in latches_and_restricted_funs:
                    self.aig.set_lit2bdd(l.next, f)
            else:
                print "BAD"
                sys.exit(0)
                # It's not worth restricting the transition relation
                # Go back to no opt
                log.LOG_MSG("Not worth restricting the next functions")
                log.LOG_MSG("\t Total dag size of next funs were " +
                        str(orig_total_size) + " now " + str(rest_total_size))
                self.opt_type = 1

    def init(self):
        return self.aig.init_state_bdd()

    def error(self):
        if self.short_error is not None:
            return self.short_error
        else:
            return self.aig.lit2bdd(self.aig.error_fake_latch.lit)

    def short_aig_error(self, error):
        self.aig = self.aig.short_error(error)

    def short_aig_error(self, errs):
        self.aig = self.aig.short_error_list(errs)

    def upre(self, dst):
        if (self.opt_type == 2):
            # log.LOG_MSG("UPRE with opt_type 2")
            return self.aig.upre_bdd_opt2(dst, use_trans=self.use_trans)
        if (self.opt_type == 3):
            # log.LOG_MSG("UPRE with opt_type: " + str(self.opt_type))
            over_upre = self.aig.upre_bdd(dst, use_trans=self.use_trans)
            return over_upre & self.coreachables()
        if (self.opt_type == 4):
            # log.LOG_MSG("UPRE with opt_type: " + str(self.opt_type))
            #upre1 = self.aig.upre_bdd(dst, use_trans=self.use_trans)
            return self.aig.upre_bdd_opt4(dst, use_trans=self.use_trans)
            #assert(upre1 | dst == upre4 | dst)
            #return upre4
        if (self.opt_type == 5):
            return self.aig.upre_bdd_opt5(dst, use_trans=self.use_trans)
        # if self.opt_type == 1
        # log.LOG_MSG("UPRE with opt_type 1")
        return self.aig.upre_bdd(dst, use_trans=self.use_trans)

    def cpre(self, dst, get_strat=False):
        return self.aig.cpre_bdd(
            dst,
            use_trans=self.use_trans, get_strat=get_strat)

    def coreachables(self):
        if (self.coreachable_states is not None):
            return self.coreachable_states
        self.coreachable_states = self.error()
        self.coreachable_states = fixpoint(
            self.coreachable_states,
            fun=lambda x: x | self.aig.pre_bdd(x)
        )
        return self.coreachable_states


class SymblicitGame(ForwardGame):
    def __init__(self, aig):
        self.aig = aig
        self.uinputs = [x.lit for x in
                        self.aig.iterate_uncontrollable_inputs()]
        self.latches = [x.lit for x in self.aig.iterate_latches()]
        self.latch_cube = BDD.make_cube(imap(funcomp(BDD,
                                                     symbol_lit),
                                             self.aig.iterate_latches()))
        self.platch_cube = BDD.make_cube(imap(funcomp(BDD,
                                                      self.aig.get_primed_var,
                                                      symbol_lit),
                                              self.aig.iterate_latches()))
        self.cinputs_cube = BDD.make_cube(
            imap(funcomp(BDD, symbol_lit),
                 self.aig.iterate_controllable_inputs()))
        self.pcinputs_cube = self.aig.prime_all_inputs_in_bdd(
            self.cinputs_cube)
        self.uinputs_cube = BDD.make_cube(
            imap(funcomp(BDD, symbol_lit),
                 self.aig.iterate_uncontrollable_inputs()))
        self.init_state_bdd = self.aig.init_state_bdd()
        self.error_bdd = self.aig.lit2bdd(self.aig.error_fake_latch.lit)
        self.Venv = dict()
        self.Venv[self.init_state_bdd] = True
        self.succ_cache = dict()

    def init(self):
        return self.init_state_bdd

    def error(self):
        return self.error_bdd

    def upost(self, q):
        assert isinstance(q, BDD)
        if q in self.succ_cache:
            return iter(self.succ_cache[q])
        A = BDD.true()
        M = set()
        while A != BDD.false():
            a = A.get_one_minterm(self.uinputs)
            trans = BDD.make_cube(
                imap(lambda x: BDD.make_eq(BDD(self.aig.get_primed_var(x.lit)),
                                           self.aig.lit2bdd(x.next)
                                           .and_abstract(q, self.latch_cube)),
                     self.aig.iterate_latches()))
            lhs = trans & a
            rhs = self.aig.prime_all_inputs_in_bdd(trans)
            simd = BDD.make_impl(lhs, rhs).univ_abstract(self.platch_cube)\
                .exist_abstract(self.pcinputs_cube)\
                .univ_abstract(self.cinputs_cube)
            simd = self.aig.unprime_all_inputs_in_bdd(simd)

            A &= ~simd
            Mp = set()
            for m in M:
                if not (BDD.make_impl(m, simd) == BDD.true()):
                    Mp.add(m)
            M = Mp
            M.add(a)
        log.DBG_MSG("Upost |M| = " + str(len(M)))
        self.succ_cache[q] = map(lambda x: (q, x), M)
        return iter(self.succ_cache[q])

    def cpost(self, s):
        assert isinstance(s, tuple)
        q = s[0]
        au = s[1]
        if s in self.succ_cache:
            L = self.succ_cache[s]
        else:
            L = BDD.make_cube(
                imap(lambda x: BDD.make_eq(BDD(x.lit),
                                           self.aig.lit2bdd(x.next)
                                           .and_abstract(q & au,
                                                         self.latch_cube &
                                                         self.uinputs_cube)),
                     self.aig.iterate_latches()))\
                .exist_abstract(self.cinputs_cube)
            self.succ_cache[s] = L
        M = set()
        while L != BDD.false():
            l = L.get_one_minterm(self.latches)
            L &= ~l
            self.Venv[l] = True
            M.add(l)
        log.DBG_MSG("Cpost |M| = " + str(len(M)))
        return iter(M)

    def is_env_state(self, s):
        return s in self.Venv
