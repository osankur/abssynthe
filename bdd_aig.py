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
along with AbsSynthe. If not, see <http://www.gnu.org/licenses/>.


Guillermo A. Perez
Universite Libre de Bruxelles
gperezme@ulb.ac.be
"""
import sys
from itertools import imap, chain, combinations
from utils import funcomp
from aig import (
    AIG,
    strip_lit,
    lit_is_negated,
    symbol_lit,
    negate_lit
)
from cudd_bdd import BDD
import log

class BDDAIG(AIG):
    def __init__(self, aig=None, aiger_file_name=None,
                 intro_error_latch=False):
        assert aig is not None or aiger_file_name is not None
        if aig is None:
            aig = AIG(aiger_file_name, intro_error_latch=intro_error_latch)
        self._copy_from_aig(aig)
        # initialize local attributes
        self.lit_to_bdd = dict()
        self.bdd_to_lit = dict()
        self._cached_transition = None
        self.bdd_gate_cache = dict()
        self.latch_restr = None
        # Successor relation without the
        # inputs
        self.post_rel = None
        # List of pairs BDD * variable set, ( l' <-> T_l, vars) 
        # where vars are to be quantified away when conjoining from left to
        # right the BDDs (l' <-> T_l) to construct the transition relation
        self.trans_order = None

    def _copy_from_aig(self, aig):
        assert isinstance(aig, AIG)
        # shallow copy of all attributes of aig
        self.__dict__ = aig.__dict__.copy()

    def set_lit2bdd(self, lit, b):
        self.lit_to_bdd[lit] = b
        return self

    def rem_lit2bdd(self, lit):
        del self.lit_to_bdd[lit]
        return self

    def get_bdd_deps(self, b):
        bdd_deps = set(b.occ_sem())
        bdd_latch_deps = bdd_deps & set([symbol_lit(x) for x
                                         in self.iterate_latches()])
        deps = reduce(set.union,
                      map(self.get_lit_deps,
                          bdd_latch_deps),
                      bdd_deps)
        return deps
    def get_bdd_latch_deps(self, b):
        bdd_latch_deps = set(b.occ_sem(imap(symbol_lit,
                                            self.iterate_latches())))
        latch_deps = reduce(set.union,
                            map(self.get_lit_latch_deps,
                                bdd_latch_deps),
                            set())
        return latch_deps

    # note that this will NOT restrict the error function
    def restrict_latch_next_funs(self, b):
        log.DBG_MSG("Restricting next funs")
        for l in self.iterate_latches():
            if l != self.error_fake_latch:
                self.set_lit2bdd(l.next,
                                 self.lit2bdd(l.next).safe_restrict(b))
                                 # self.lit2bdd(l.next) & b)

    # add b to the error function as a disjunct
    def add_error(self, b):
        nu_bddaig = BDDAIG(aig=self)
        nu_bddaig.set_lit2bdd(self.error_fake_latch.next, 
                nu_bddaig.lit2bdd(self.error_fake_latch.next) | b)
        return nu_bddaig

    # short-circuit the error bdd to b and restrict to cone(b)
    def short_error(self, b):
        nu_bddaig = BDDAIG(aig=self)
        nu_bddaig.set_lit2bdd(self.error_fake_latch.next, b)
        latch_deps = self.get_bdd_latch_deps(b)
        if log.debug:
            not_deps = [l.lit for l in self.iterate_latches()
                        if l.lit not in latch_deps]
            log.DBG_MSG(str(len(not_deps)) + " Latches not needed")
        nu_bddaig.latch_restr = latch_deps
        return nu_bddaig

    # short-circuit the error bdd to b and restrict the trans functions
    # to ~b
    def short_error_restrict(self, b):
        nu_bddaig = BDDAIG(aig=self)
        nu_bddaig.set_lit2bdd(self.error_fake_latch.next, b)
        latch_deps = self.get_bdd_latch_deps(b)
        if log.debug:
            not_deps = [l.lit for l in self.iterate_latches()
                        if l.lit not in latch_deps]
            log.DBG_MSG(str(len(not_deps)) + " Latches not needed")
        nu_bddaig.latch_restr = latch_deps
        # nu_bddaig.restrict_latch_next_funs(~b)
        return nu_bddaig

    def iterate_latches(self):
        for l in AIG.iterate_latches(self):
            if self.latch_restr is not None and\
                    l.lit not in self.latch_restr and\
                    l != self.error_fake_latch:
                # log.DBG_MSG("ignoring latch " + str(l.lit))
                continue
            yield l

    def lit2bdd(self, lit):
        """ Convert AIGER lit into BDD """
        # query cache
        if lit in self.lit_to_bdd:
            return self.lit_to_bdd[lit]
        # get stripped lit
        stripped_lit = strip_lit(lit)
        (intput, latch, and_gate) = self.get_lit_type(stripped_lit)
        # is it an input, latch, gate or constant
        if intput or latch:
            result = BDD(stripped_lit)
        elif and_gate:
            result = (self.lit2bdd(and_gate.rhs0) &
                      self.lit2bdd(and_gate.rhs1))
        else:  # 0 literal, 1 literal and errors
            result = BDD.false()
        # cache result
        self.lit_to_bdd[stripped_lit] = result
        self.bdd_to_lit[result] = stripped_lit
        # check for negation
        if lit_is_negated(lit):
            result = ~result
            self.lit_to_bdd[lit] = result
            self.bdd_to_lit[result] = lit
            # latch_funs = [self.lit2bdd(x.next) for x in
            #               self.iterate_latches()]
        return result

    def prime_latches_in_bdd(self, b):
        # unfortunately swap_variables needs a list
        latches = [x.lit for x in self.iterate_latches()]
        platches = map(self.get_primed_var, latches)
        return b.swap_variables(latches, platches)

    def prime_all_inputs_in_bdd(self, b):
        # unfortunately swap_variables needs a list
        inputs = [x.lit for x in chain(self.iterate_uncontrollable_inputs(),
                                       self.iterate_controllable_inputs())]
        pinputs = map(self.get_primed_var, inputs)
        return b.swap_variables(inputs, pinputs)

    def unprime_all_inputs_in_bdd(self, b):
        # unfortunately swap_variables needs a list
        inputs = [x.lit for x in chain(self.iterate_uncontrollable_inputs(),
                                       self.iterate_controllable_inputs())]
        pinputs = map(self.get_primed_var, inputs)
        return b.swap_variables(pinputs, inputs)

    def unprime_latches_in_bdd(self, b):
        # unfortunately swap_variables needs a list
        latches = [x.lit for x in self.iterate_latches()]
        platches = map(self.get_primed_var, latches)
        return b.swap_variables(platches, latches)

    def trans_rel_bdd(self):
        # check cache
        if self._cached_transition is not None:
            return self._cached_transition
        b = BDD.true()
        for x in self.iterate_latches():
            b &= BDD.make_eq(BDD(self.get_primed_var(x.lit)),
                             self.lit2bdd(x.next))
        self._cached_transition = b
        log.BDD_DMP(b, "Composed and cached the concrete transition relation.")
        return b

    def init_state_bdd(self):
        b = BDD.true()
        for x in self.iterate_latches():
            b &= ~BDD(x.lit)
        return b

    def over_post_bdd(self, src_states_bdd, sys_strat=None):
        """ Over-approximated version of concrete post which can be done even
        without the transition relation """
        strat = BDD.true()
        if sys_strat is not None:
            strat &= sys_strat
        # to do this, we use an over-simplified transition relation, EXu,Xc
        b = BDD.true()
        for x in self.iterate_latches():
            temp = BDD.make_eq(BDD(self.get_primed_var(x.lit)),
                               self.lit2bdd(x.next))
            b &= temp.and_abstract(
                strat,
                BDD.make_cube(imap(
                    funcomp(BDD, symbol_lit),
                    self.iterate_controllable_inputs()
                )))
            b = b.restrict(src_states_bdd)
        b &= src_states_bdd
        b = b.exist_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                          chain(self.iterate_latches(),
                                self.iterate_uncontrollable_inputs()))))
        return self.unprime_latches_in_bdd(b)

    def post_monolithic_bdd(self, src_states_bdd, sys_strat=None):
        latches = [x for x in self.iterate_latches()]
        latch_cube = BDD.make_cube(imap(funcomp(BDD, symbol_lit),latches))
        trans_src = src_states_bdd & self.trans_rel_bdd()
        vars = [x for x in self.iterate_controllable_inputs()] + [x for x in self.iterate_uncontrollable_inputs()]
        vars = vars + latches
        cube = BDD.make_cube(imap(funcomp(BDD, symbol_lit), vars))
        return self.unprime_latches_in_bdd(trans_src.exist_abstract(cube))

    def post_bdd(self, src_states_bdd, sys_strat=None):
        b_trans = False
        W1 = 2
        W2 = 1
        W4 = 1
        P = []
        latches = [x for x in self.iterate_latches()]
        latch_cube = BDD.make_cube(imap(funcomp(BDD, symbol_lit),latches))
        inputs = [x for x in self.iterate_controllable_inputs()] + [x for x in self.iterate_uncontrollable_inputs()]
        latch_lits = set(map(symbol_lit, latches))
        input_lits = set(map(symbol_lit, inputs))
        # transition relation for each latch
        trans = map(lambda l: BDD.make_eq(BDD(self.get_primed_var(l.lit)), self.lit2bdd(l.next)), latches)
        # Q is the list of pairs of latches and their trans relations except for err latch, 
        # for which we conjoin with src_states_bdd
        log.DBG_MSG("Doing err_fun & src_states")
        if b_trans:
            Q = zip(latches,trans)
        else:
            err_latch = self.error_fake_latch
            Q = []
            for (q,b) in zip(latches,trans):
                if (q == err_latch):
                    Q.append((q, b & src_states_bdd))
                else:
                    Q.append((q, b))
        log.DBG_MSG("Launching Clustering")
        if b_trans:
            caredVars = input_lits
        else:
            caredVars = latch_lits | input_lits
        Q = set(Q)
        while len(Q) != 0:
            v = []
            m = []
            # The list of sets of dependent variables for each element of Q
            deps = map(lambda b: set(b[1].occ_sem(caredVars)),Q)
            # deps = map(lambda b: set(self.get_bdd_deps(b)) & caredVars,Qbdd)
            allQdeps = reduce(lambda x,y: x|y, deps);
            # The list of sets of BDD indices of the dependent variables ...
            dep_indices = map(lambda s: map(lambda b: BDD(b).get_index(),s), deps)
            dep_indices = map(lambda s: set([0]) if (len(s) == 0) else s, dep_indices)
            w = map(lambda s: len(s), deps)
            m = map(lambda s: max(s), dep_indices)
            M = max(m)
            x = len(allQdeps);
            for (q,qdep) in zip(Q,deps):
                vset = qdep
                for (u,udep) in zip(Q,deps):
                    if u == q:
                        continue
                    vset = vset - udep
                v.append(len(vset))
            # total scores
            R = []
            for (ve,we,me,q) in zip(v,w,m,Q):
                if (we == 0):
                    r1 = 0
                else:
                    r1 = ve / float(we)
                r2 = we / float(x)
                r4 = me / float(M)
                R.append((q,W1 * r1 + W2 * r2 + W4*r4))
            qselected = min(R, key=lambda (x,y): y)[0]
            Q = Q - set([qselected])
            P.append(qselected)
        # Reminder: we want to conjoin all elements of P[1]
        # Computing the quantification schedule
        var_clusters = []
        acc = set([])
        for p in P:
            newvars = set(p[1].occ_sem(caredVars)) - acc
            var_clusters.append(newvars)
            acc = acc | newvars
        cj = zip(var_clusters, map(lambda l: l[0].lit, P))
        for (vars,l) in cj:
            print "Latch ", l, " : ", vars
        print "All variables to be quantified: ", sorted(list(acc))
        PT = map(lambda x: x[1], P)
        post = BDD.true()
        log.DBG_MSG("Ending Clustering")
        for (var, con) in reversed(zip(var_clusters,PT)):
            post &= con
            if (var):
                post = post.exist_abstract(BDD.make_cube(imap(BDD,var)))
        if b_trans:
            post = self.unprime_latches_in_bdd((src_states_bdd & post).exist_abstract(latch_cube))
        else:
            post = self.unprime_latches_in_bdd(post)
        return post


    #def post_bdd(self, src_states_bdd, sys_strat=None,
    #             use_trans=False, over_approx=False):
    #    """
    #    POST = EL.EXu.EXc : src(L) ^ T(L,Xu,Xc,L') [^St(L,Xu,Xc)]
    #    optional argument fixes possible actions for the environment
    #    """
    #    if not use_trans or over_approx:
    #        return self.over_post_bdd(src_states_bdd, sys_strat)
    #    transition_bdd = self.trans_rel_bdd()
    #    trans = transition_bdd
    #    if sys_strat is not None:
    #        trans &= sys_strat
    #    trans = trans.restrict(src_states_bdd)

    #    suc_bdd = trans.and_abstract(
    #        src_states_bdd,
    #        BDD.make_cube(imap(funcomp(BDD, symbol_lit), chain(
    #            self.iterate_controllable_inputs(),
    #            self.iterate_uncontrollable_inputs(),
    #            self.iterate_latches())
    #        )))
    #    return self.unprime_latches_in_bdd(suc_bdd)

    

    def substitute_latches_next_orig(self, b, use_trans=False, restrict_fun=None):
        if use_trans:
            transition_bdd = self.trans_rel_bdd()
            trans = transition_bdd
            if restrict_fun is not None:
                trans = trans.restrict(restrict_fun)
            primed_bdd = self.prime_latches_in_bdd(b)
            primed_latches = BDD.make_cube(
                imap(funcomp(BDD, self.get_primed_var, symbol_lit),
                     self.iterate_latches()))
            return trans.and_abstract(primed_bdd,
                                      primed_latches)
        else:
            latches = [x.lit for x in self.iterate_latches()]
            latch_funs = [self.lit2bdd(x.next) for x in
                          self.iterate_latches()]
            if restrict_fun is not None:
                latch_funs = [x.restrict(restrict_fun) for x in latch_funs]
            # take a transition step backwards
            return b.compose(latches, latch_funs)

    def substitute_latches_next(self, b, use_trans=False, restrict_fun=None):
        if use_trans:
            transition_bdd = self.trans_rel_bdd()
            trans = transition_bdd
            if restrict_fun is not None:
                for f in restrict_fun:
                    trans = trans.restrict(f)
            primed_bdd = self.prime_latches_in_bdd(b)
            primed_latches = BDD.make_cube(
                imap(funcomp(BDD, self.get_primed_var, symbol_lit),
                     self.iterate_latches()))
            return trans.and_abstract(primed_bdd,
                                      primed_latches)
        else:
            latches = [x.lit for x in self.iterate_latches()]
            latch_funs = [self.lit2bdd(x.next) for x in
                          self.iterate_latches()]
            ######## This restrict *does* help sometimes reduce the BDD sizes
            if restrict_fun is not None:
                orig_size = reduce(lambda x,y:x+y, [l.dag_size() for l in latch_funs])
                # log.BDD_DMP(latch_funs[34], "fun[0]")
                for f in restrict_fun:
                    latch_funs = [x.restrict(f) for x in latch_funs]
                after_size = reduce(lambda x,y:x+y, [l.dag_size() for l in latch_funs])
                #if (orig_size > after_size):
                #    print "IMPROVEMENT: ", orig_size, after_size
                #else:
                #    print "No improvement", orig_size
            return b.compose(latches, latch_funs)

    def upre_bdd(self, dst_states_bdd, env_strat=None, get_strat=False,
                 use_trans=False):
        """
        UPRE = EXu.AXc.EL' : T(L,Xu,Xc,L') ^ dst(L') [^St(L,Xu)]
        """
        # take a transition step backwards
        # TECH NOTE: the restrict_fun=~dst... works ONLY because I will use the
        # result and take the union with dst_states afterwards...
        p_bdd = self.substitute_latches_next(
            dst_states_bdd,
            restrict_fun=[~dst_states_bdd],
            use_trans=use_trans)
        # use the given strategy
        if env_strat is not None:
            p_bdd &= env_strat
        # there is an uncontrollable action such that for all contro...
        temp_bdd = p_bdd.univ_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               self.iterate_controllable_inputs())))
        p_bdd = temp_bdd.exist_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               self.iterate_uncontrollable_inputs())))
        # prepare the output
        if get_strat:
            return temp_bdd
        else:
            return p_bdd

    def overpre_bdd(self, dst_states_bdd):
        latches = [x for x in self.iterate_latches()]
        nlatches = len(latches)
        if (nlatches > 40):
            remlatches = latches[0:nlatches/2]
            latches = latches[nlatches/2:]
            dst_states_bdd = dst_states_bdd.exist_abstract(
                    BDD.make_cube(map(funcomp(BDD,symbol_lit),remlatches)))
        latch_funs = [self.lit2bdd(x.next) for x in latches]
        latches = map(symbol_lit, latches)
        tmp_bdd = dst_states_bdd.compose(latches, latch_funs)
        #tmp_bdd = tmp_bdd.exist_abstract(
        #    BDD.make_cube(imap(funcomp(BDD, symbol_lit),
        #                       self.iterate_controllable_inputs())))
        inputs = list(self.iterate_controllable_inputs()) + list(self.iterate_uncontrollable_inputs())
        one_step_pre = tmp_bdd.exist_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               inputs)))
        #one_step_pre = tmp_bdd.exist_abstract(
        #    BDD.make_cube(imap(funcomp(BDD, symbol_lit),
        #                       self.iterate_inputs())))
        return one_step_pre

    def pre_bdd(self, dst_states_bdd):
        latches = [x.lit for x in self.iterate_latches()]
        latch_funs = [self.lit2bdd(x.next) for x in
                      self.iterate_latches()]
        tmp_bdd = dst_states_bdd.compose(latches, latch_funs)
        tmp_bdd = tmp_bdd.exist_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               self.iterate_controllable_inputs())))
        one_step_pre = tmp_bdd.exist_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               self.iterate_uncontrollable_inputs())))
        return one_step_pre

    def upre_bdd_opt2(self, dst_states_bdd, env_strat=None, get_strat=False, 
                    use_trans=False):
        """
        This optimization consists in computing the predecessors,
        restricting the transition functions to Pre, 
        applying upre and intersecting back with Pre.

        This optimization did help reduce BDD sizes, often very modestly
        sometimes a bit more. But the computation overhead was too much

        One could also use overpre which gives the same result and
        the only improvement (if any) seems to be due to unpredictable variable
        reordering
        """
        one_step_pre = self.pre_bdd(dst_states_bdd)
        p_bdd = self.substitute_latches_next(
            dst_states_bdd,
            restrict_fun=[~dst_states_bdd, one_step_pre],
            #restrict_fun=[one_step_pre],
            use_trans=use_trans)
        p_bdd &= one_step_pre
        # use the given strategy
        if env_strat is not None:
            p_bdd &= env_strat
        # there is an uncontrollable action such that for all contro...
        temp_bdd = p_bdd.univ_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               self.iterate_controllable_inputs())))
        p_bdd = temp_bdd.exist_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               self.iterate_uncontrollable_inputs())))
        # prepare the output
        if get_strat:
            return temp_bdd
        else:
            return p_bdd

    def upre_bdd_opt5(self, dst_states_bdd, env_strat=None, get_strat=False, 
                    use_trans=False):
        """
            Nothing...........
        """
        all_cinputs = [x.lit for x in self.iterate_controllable_inputs()]
        latch_names = list(self.iterate_latches())
        cinputs = map(lambda x: self.lit2bdd(x.next).occ_sem(all_cinputs), latch_names)
        pairs = zip(latch_names, cinputs)
        nocinput_latches = filter(lambda x: len(x[1]) == 0, pairs)
        cinput_latches = filter(lambda x: len(x[1]) > 0, pairs)

        # COMPOSE
        restr_fun = [~dst_states_bdd]
        latch_funs = map(lambda x: self.lit2bdd(x[0].next), nocinput_latches)
        latches = map(lambda x: x.lit, nocinput_latches)
        for f in restrict_fun:
            latch_funs = [x.restrict(f) for x in latch_funs]
        pre = b.compose(latches, latch_funs)
        #/COMPOSE

        if env_strat is not None:
            p_bdd &= env_strat
        # there is an uncontrollable action such that for all contro...
        temp_bdd = p_bdd.univ_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               self.iterate_controllable_inputs())))
        p_bdd = temp_bdd.exist_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               self.iterate_uncontrollable_inputs())))
        # prepare the output
        if get_strat:
            return temp_bdd
        else:
            return p_bdd

    def upre_bdd_opt4(self, dst_states_bdd, env_strat=None, get_strat=False,
                 use_trans=False):
        """
        This optimization consists in manually expanding the universal
        quantificaton for a small number of cinputs (exp_unfold_bound),
        distributing the remaining universal quantification inside conjuncts,
        and then applying quant. scheduling to apply the existential quant.
        """
        restr_opt = False
        exp_unfold_bound = 1
        p_bdd = self.substitute_latches_next(
            dst_states_bdd,
            restrict_fun=[~dst_states_bdd],
            use_trans=use_trans)
        if env_strat is not None:
            p_bdd &= env_strat
        def powerset(iterable):
          xs = list(iterable)
          return chain.from_iterable( combinations(xs,n) for n in range(len(xs)+1) )
        # We apply the universal quantifier manually for the subset exp_cinputs
        cinputs = list(self.iterate_controllable_inputs())
        # cinputs.reverse()
        exp_cinputs = cinputs[0:exp_unfold_bound]
        rest_cinputs = cinputs[exp_unfold_bound:]
        # assert(set(exp_cinputs) | set(rest_cinputs) == set(cinputs))
        rest_cinputs_cube = BDD.make_cube(imap(funcomp(BDD,symbol_lit), rest_cinputs))
        conjuncts = []
        # p_bdd = p_bdd.univ_abstract(rest_cinputs_cube)
        for inp in powerset(exp_cinputs):
            pos_latches = map(symbol_lit,inp)
            neg_latches = list(map(symbol_lit,set(exp_cinputs)-set(inp)))
            some_latches = pos_latches + neg_latches
            some_values = ([BDD.true()] * len(pos_latches)) + ([BDD.false()]*len(neg_latches))
            tmp = p_bdd.compose(some_latches,some_values)
            # alternative to compose:
            # tmp = p_bdd
            # for lat in pos_latches:
            #     tmp &= BDD(lat)
            # for lat in neg_latches:
            #    tmp &= ~BDD(lat)
            # tmp = tmp.exist_abstract(BDD.make_cube(imap(BDD,some_latches)))
            conjuncts.append(tmp.univ_abstract(rest_cinputs_cube))
            # conjuncts.append(tmp)
        uinput_vars = map(symbol_lit, self.iterate_uncontrollable_inputs())
        # Sort the conjuncts in increasing order of their occ_sem(uinputs)
        conjuncts.sort(lambda c,d:
                cmp(len(c.occ_sem(uinput_vars)),len(d.occ_sem(uinput_vars))))
        # occ_vars = map(lambda x: x.occ_sem(uinput_vars),conjuncts)
        # for l in occ_vars:
        # print l
        # var_clusters[i] will contain the variables that only appear
        # in var_clusters[i:]
        var_clusters = []
        acc = set([])
        for i in range(len(conjuncts)):
            newvars = set(conjuncts[i].occ_sem(uinput_vars)) - acc
            var_clusters.append(newvars)
            acc = acc | newvars
        # Compute conjunction inside out
        log.DBG_MSG("Quantification schedule:")
        for l in var_clusters:
            log.DBG_MSG(str(l))
        # print "Uinput dependencies of the conjuncts:"
        # occ_vars = map(lambda x: x.occ_sem(uinput_vars),conjuncts)
        # for l in occ_vars:
        #    print l
        # assert(upre_LXu == self.upre_bdd(dst_states_bdd,
        #            get_strat=True,use_trans=use_trans))
        upre_L = BDD.true()
        for (var, con) in reversed(zip(var_clusters, conjuncts)):
            upre_L &= con
            if (var):
                upre_L = upre_L.exist_abstract(BDD.make_cube(imap(BDD, var)))
        # p_bdd = upre_LXu.exist_abstract(
        #  BDD.make_cube(imap(funcomp(BDD, symbol_lit),
        #                     self.iterate_uncontrollable_inputs())))
        #assert(p_bdd == upre_L)
        # assert(upre_L == self.upre_bdd(dst_states_bdd,use_trans=use_trans))
        # assert(upre_L == noopt_upre)
        if get_strat:
            return reduce(lambda x,y: x&y, conjuncts)
        else:
            return upre_L

    def cpre_bdd(self, dst_states_bdd, get_strat=False, use_trans=False):
        """ CPRE = AXu.EXc.EL' : T(L,Xu,Xc,L') ^ dst(L') """
        # take a transition step backwards
        p_bdd = self.substitute_latches_next(dst_states_bdd,
                                             use_trans=use_trans)
        # for all uncontrollable action there is a contro...
        # note: if argument get_strat == True then we leave the "good"
        # controllable actions in the bdd
        if not get_strat:
            p_bdd = p_bdd.exist_abstract(
                BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                                   self.iterate_controllable_inputs())))
            p_bdd = p_bdd.univ_abstract(
                BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                                   self.iterate_uncontrollable_inputs())))
        return p_bdd

    def strat_is_inductive(self, strat, use_trans=False):
        strat_dom = strat.exist_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               chain(self.iterate_controllable_inputs(),
                                     self.iterate_uncontrollable_inputs()))))
        p_bdd = self.substitute_latches_next(strat_dom, use_trans=use_trans)
        return BDD.make_impl(strat, p_bdd) == BDD.true()

    def get_optimized_and_lit(self, a_lit, b_lit):
        if a_lit == 0 or b_lit == 0:
            return 0
        if a_lit == 1 and b_lit == 1:
            return 1
        if a_lit == 1:
            return b_lit
        if b_lit == 1:
            return a_lit
        if a_lit > 1 and b_lit > 1:
            a_b_lit = self.next_lit()
            self.add_gate(a_b_lit, a_lit, b_lit)
            return a_b_lit
        assert 0, 'impossible'

    def bdd2aig(self, a_bdd):
        """
        Walk given BDD node (recursively). If given input BDD requires
        intermediate AND gates for its representation, the function adds them.
        Literal representing given input BDD is `not` added to the spec.
        """
        if a_bdd in self.bdd_gate_cache:
            return self.bdd_gate_cache[a_bdd]

        if a_bdd.is_constant():
            res = int(a_bdd == BDD.true())   # in aiger 0/1 = False/True
            return res
        # get an index of variable,
        # all variables used in bdds also introduced in aiger,
        # except fake error latch literal,
        # but fake error latch will not be used in output functions (at least
        # we don't need this..)
        a_lit = a_bdd.get_index()
        assert (a_lit != self.error_fake_latch.lit),\
               ("using error latch in the " +
                "definition of output " +
                "function is not allowed")
        t_bdd = a_bdd.then_child()
        e_bdd = a_bdd.else_child()
        t_lit = self.bdd2aig(t_bdd)
        e_lit = self.bdd2aig(e_bdd)
        # ite(a_bdd, then_bdd, else_bdd)
        # = a*then + !a*else
        # = !(!(a*then) * !(!a*else))
        # -> in general case we need 3 more ANDs
        a_t_lit = self.get_optimized_and_lit(a_lit, t_lit)
        na_e_lit = self.get_optimized_and_lit(negate_lit(a_lit), e_lit)
        n_a_t_lit = negate_lit(a_t_lit)
        n_na_e_lit = negate_lit(na_e_lit)
        ite_lit = self.get_optimized_and_lit(n_a_t_lit, n_na_e_lit)
        res = negate_lit(ite_lit)
        if a_bdd.is_complement():
            res = negate_lit(res)
        # cache result
        self.bdd_gate_cache[a_bdd] = res
        return res

    # Given a bdd representing the set of safe states-action pairs for the
    # controller (Eve) we compute a winning strategy for her (trying to get a
    # minimal one via a greedy algo on the way).
    def extract_output_funs(self, strategy, care_set=None):
        """
        Calculate BDDs for output functions given non-deterministic winning
        strategy.
        """
        if care_set is None:
            care_set = BDD.true()

        output_models = dict()
        all_outputs = [BDD(x.lit) for x in self.iterate_controllable_inputs()]
        for c_symb in self.iterate_controllable_inputs():
            c = BDD(c_symb.lit)
            others = set(set(all_outputs) - set([c]))
            if others:
                others_cube = BDD.make_cube(others)
                c_arena = strategy.exist_abstract(others_cube)
            else:
                c_arena = strategy
            # pairs (x,u) in which c can be true
            can_be_true = c_arena.cofactor(c)
            # pairs (x,u) in which c can be false
            can_be_false = c_arena.cofactor(~c)
            must_be_true = (~can_be_false) & can_be_true
            must_be_false = (~can_be_true) & can_be_false
            local_care_set = care_set & (must_be_true | must_be_false)
            # Restrict operation:
            #   on care_set: must_be_true.restrict(care_set) <-> must_be_true
            c_model = min([must_be_true.safe_restrict(local_care_set),
                          (~must_be_false).safe_restrict(local_care_set)],
                          key=lambda x: x.dag_size())
            output_models[c_symb.lit] = c_model
            log.DBG_MSG("Size of function for " + str(c.get_index()) + " = " +
                        str(c_model.dag_size()))
            strategy &= BDD.make_eq(c, c_model)
        return output_models