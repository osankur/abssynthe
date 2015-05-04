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
from algos import (
    BackwardGame,
    backward_safety_synth
)
from aig import (
    strip_lit,
    lit_is_negated
)
from cudd_bdd import BDD
from bdd_aig import BDDAIG
from bdd_games import ConcGame
import log

def merge_some_signals(cube, C, aig, argv):
    # TODO: there must be a more pythonic way of doing all of this
    log.LOG_MSG(str(len(C)) + " sub-games originally")
    cube_deps = aig.get_bdd_deps(cube)
    dep_map = dict()
    for c in C:
        deps = frozenset(cube_deps | aig.get_lit_deps(c))
        found = False
        for key in dep_map:
            if key >= deps:
                dep_map[key] &= aig.lit2bdd(c)
                found = True
                break
            elif key <= deps:
                dep_map[deps] = dep_map[key] & aig.lit2bdd(c)
                del dep_map[key]
                found = True
                break
        if not found:
            dep_map[deps] = aig.lit2bdd(c)
    log.LOG_MSG(str(len(dep_map.keys())) + " sub-games after incl. red.")
    for key in dep_map:
        yield ~dep_map[key] & cube


def decompose(aig, argv):
    if argv.decomp == 1:
        if lit_is_negated(aig.error_fake_latch.next):
            log.DBG_MSG("Decomposition opt possible (BIG OR case)")
            (A, B) = aig.get_1l_land(strip_lit(aig.error_fake_latch.next))
            return imap(lambda a: ConcGame(
                BDDAIG(aig).short_error(a),
                use_trans=argv.use_trans),
                merge_some_signals(BDD.true(), A, aig, argv))
        else:
            (A, B) = aig.get_1l_land(aig.error_fake_latch.next)
            if not B:
                log.DBG_MSG("No decomposition opt possible")
                return None
            else:
                log.DBG_MSG("Decomposition opt possible (A ^ [C v D] case)")
                log.DBG_MSG(str(len(A)) + " AND leaves: " + str(A))
            # critical heuristic: which OR leaf do we distribute?
            # here I propose to choose the one with the most children
            b = B.pop()
            (C, D) = aig.get_1l_land(b)
            for bp in B:
                (Cp, Dp) = aig.get_1l_land(bp)
                if len(Cp) > len(C):
                    b = bp
                    C = Cp
            log.DBG_MSG("Chosen OR: " + str(b))
            rem_AND_leaves = filter(lambda x: strip_lit(x) != b, A)
            rdeps = set()
            for r in rem_AND_leaves:
                rdeps |= aig.get_lit_latch_deps(strip_lit(r))
            log.DBG_MSG("Rem. AND leaves' deps: " + str(rdeps))
            cube = BDD.make_cube(map(aig.lit2bdd, rem_AND_leaves))
            log.DBG_MSG(str(len(C)) + " OR leaves: " +
                        str(map(aig.get_lit_name, C)))
            return imap(lambda a: ConcGame(
                BDDAIG(aig).short_error(a),
                use_trans=argv.use_trans), merge_some_signals(cube, C, aig,
                                                              argv))
    elif argv.decomp == 2:
        raise NotImplementedError


def get_cinputs_of_game(game):
    cinputs = set()
    all_cinputs = [x.lit for x in game.aig.iterate_controllable_inputs()]
    for l in game.aig.iterate_latches():
        cinputs |= set(game.aig.lit2bdd(l.next).occ_sem(all_cinputs))
    return cinputs
    

# Compositional approach, receives an iterable of BackwardGames
def comp_synth(games):
    s = BDD.true()
    cum_w = BDD.true()
    cnt = 0
    sub_w = []
    # We will iterate several times over games!
    games = list(games)
    # If all subgames have each one latch (i.e. error latch) 
    # then the global game has the error latch
    b_latchless = all(map(lambda g: g.aig.num_latches() == 0, games))
    cinputs = map(get_cinputs_of_game, games)
    def aux(x,y):
        if (len(x&y)>0):
            raise Exception()
        return x|y
    for c in cinputs:
        log.DBG_MSG(str(c))
    # Are the cinputs of the subgames pairwise disjoint?
    try:
        reduce(aux, cinputs, set([]))
        b_disjoint_cinputs = True
    except Exception:
        b_disjoint_cinputs = False
    log.DBG_MSG("latchless: " +str(b_latchless))
    log.DBG_MSG("disjoint cinputs: " + str(b_disjoint_cinputs))
    for game in games:
        assert isinstance(game, BackwardGame)
        w = backward_safety_synth(game)
        cpre = game.cpre(w, get_strat=True)
        cnt += 1
        # short-circuit a negative response
        if w is None:
            log.DBG_MSG("Short-circuit exit after sub-game #" + str(cnt))
            return (None, None)
        sub_w.append((w,cpre))
    if (b_latchless and b_disjoint_cinputs):
        return (~game.error(), BDD.true())
    for (w,st) in sub_w:
        # THE FOLLOWING LINE IS BUGGY
        # s &= game.cpre(w, get_strat=True)
        s &= st
        cum_w &= w
        # sanity check before moving forward
        if (not s or not game.init() & s):
            return (None, None)
    log.DBG_MSG("Solved " + str(cnt) + " sub games.")
    return (cum_w, s)


def comp_synth3(games, gen_game, use_strat=False):
    s = None
    cum_s = BDD.true()
    cum_w = BDD.true()
    cnt = 0
    triple_list = []
    for game in games:
        assert isinstance(game, BackwardGame)
        w = backward_safety_synth(game)
        cnt += 1
        # short-circuit a negative response
        if w is None:
            log.DBG_MSG("Short-circuit exit 1 after sub-game #" + str(cnt))
            return None
        if (use_strat):
            s = game.cpre(w, get_strat=True)
            cum_s &= s
            cum_w &= w
            # another short-circuit exit
            if (not cum_s or not game.init() & cum_s):
                log.DBG_MSG("Short-circuit exit 2 after sub-game #" + str(cnt))
                return None
        else:
            # s = game.cpre(w, get_strat=True)
            # cum_s &= s
            cum_w &= w
            if (not cum_w or not game.init() & cum_w):
                log.DBG_MSG("Short-circuit exit 2 after sub-game #" + str(cnt))
                return None
        triple_list.append((game, s, w))
    log.DBG_MSG("Solved " + str(cnt) + " sub games.")
    #print "---Solving global"
    #gen_game.short_aig_error(~cum_w)
    #return backward_safety_synth(gen_game)
    # if (not use_strat):
    #    cum_s = cum_w
    # lets simplify transition functions
    #if (use_strat):
    gen_game.short_aig_error(~cum_w)
    #else:
    #    gen_game.short_aig_error(~cum_w)
        
    # what comes next is a fixpoint computation using a UPRE
    # step at a time in the global game and using it to get more
    # information from the local sub-games
    lose = BDD.true()
    lose_next = ~cum_w | gen_game.error()
    while lose_next != lose:
        lose = lose_next
        log.DBG_MSG("Doing global UPRE")
        gen_game.short_aig_error(lose)
        lose_next = lose | gen_game.upre(lose)
        for i in range(len(triple_list)):
            wt = triple_list[i][2]
            gamet = triple_list[i][0]
            local_deps = set([x.lit for x in gamet.aig.iterate_latches()])
            rem_lats = gen_game.aig.get_bdd_latch_deps(lose_next) - local_deps
            pt = lose_next
            if rem_lats:
                pt = lose_next.univ_abstract(
                    BDD.make_cube(map(BDD, rem_lats)))
            # log.BDD_DMP(lose_next, "global losing area iterate")
            # log.BDD_DMP(pt, "new losing area")
            assert BDD.make_impl(~wt, pt) == BDD.true()
            if BDD.make_impl(pt, ~wt) != BDD.true():
                gamet.short_error = pt
                wt = backward_safety_synth(gamet)
                if (wt is None or not gamet.init() & wt):
                    log.DBG_MSG("Short-circuit exit 3")
                    return None
                if(use_strat):
                    st = gamet.cpre(wt, get_strat=True)
                    cum_s &= st
                    gen_game.short_aig_error(~cum_s)
                    triple_list[i] = (gamet, st, wt)
                else:
                    #gen_game.short_aig_error(~wt)
                    triple_list[i] = (gamet, None, wt)
        for t in triple_list:
            lose_next |= ~t[2]
    # after the fixpoint has been reached we can compute the error
    win = ~lose
    if (not win or not gen_game.init() & win):
        return None
    else:
        return win


def comp_synth4(games, gen_game):
    s = None
    cum_s = None
    cum_w = None
    cnt = 0
    triple_list = []
    for game in games:
        assert isinstance(game, BackwardGame)
        w = backward_safety_synth(game)
        cnt += 1
        # short-circuit a negative response
        if w is None:
            log.DBG_MSG("Short-circuit exit 1 after sub-game #" + str(cnt))
            return None
        s = game.cpre(w, get_strat=True)
        if cum_s is None:
            cum_s = s
            cum_w = w
        else:
            cum_s &= s
            cum_w &= w
        # another short-circuit exit
        if (not cum_s or not game.init() & cum_s):
            log.DBG_MSG("Short-circuit exit 2 after sub-game #" + str(cnt))
            return None
        triple_list.append((game, s, w))
    log.DBG_MSG("Solved " + str(cnt) + " sub games.")
    # lets simplify transition functions
    gen_game.aig.restrict_latch_next_funs(cum_s)
    # what comes next is a fixpoint computation using a UPRE
    # step at a time in the global game and using it to get more
    # information from the local sub-games
    lose = BDD.true()
    lose_next = ~cum_w | gen_game.error()
    while lose_next != lose:
        lose = lose_next
        log.DBG_MSG("Doing global UPRE")
        lose_next = lose | gen_game.upre(lose)
        for i in range(len(triple_list)):
            wt = triple_list[i][2]
            gamet = triple_list[i][0]
            local_deps = set([x.lit for x in gamet.aig.iterate_latches()])
            rem_lats = gen_game.aig.get_bdd_latch_deps(lose_next) - local_deps
            pt = lose_next
            if rem_lats:
                pt = lose_next.univ_abstract(
                    BDD.make_cube(map(BDD, rem_lats)))
            # log.BDD_DMP(lose_next, "global losing area iterate")
            # log.BDD_DMP(pt, "new losing area")
            assert BDD.make_impl(~wt, pt) == BDD.true()
            if BDD.make_impl(pt, ~wt) != BDD.true():
                gamet.short_error = pt
                wt = backward_safety_synth(gamet)
                if (wt is None or not gamet.init() & wt):
                    log.DBG_MSG("Short-circuit exit 3")
                    return None
                st = gamet.cpre(wt, get_strat=True)
                gen_game.aig.restrict_latch_next_funs(wt)
                triple_list[i] = (gamet, st, wt)
        for t in triple_list:
            lose_next |= ~t[2]
    # after the fixpoint has been reached we can compute the error
    win = ~lose
    if (not win or not gen_game.init() & win):
        return None
    else:
        return win


def subgame_mapper(games, aig, get_strat=False):
    s = None
    cnt = 0
    pair_list = []
    for game in games:
        assert isinstance(game, BackwardGame)
        w = backward_safety_synth(game)
        cnt += 1
        # short-circuit a negative response
        if w is None:
            log.DBG_MSG("Short-circuit exit 1 after sub-game #" + str(cnt))
            return None
        s = None
        if (get_strat):
            s = game.cpre(w, get_strat=True)
        pair_list.append((game, s, w))
    log.DBG_MSG("Solved " + str(cnt) + " sub games.")
    # lets simplify transition functions
    # aig.restrict_latch_next_funs(cum_s)
    return pair_list


def subgame_reducer(games, aig, argv, a=None, b=None, c=None, get_strat=False):
    assert games
    games = list(games)
    b_latchless = all(map(lambda g: g[0].aig.num_latches() == 0, games))
    if (b_latchless):
        log.DBG_MSG("We are going latchless!")
    if a is None:
        a = 2
    if b is None:
        b = -1
    if c is None:
        c = -1
    while len(games) >= 2:
        triple_list = []
        # we first compute an fij function for all pairs
        for i in range(0, len(games) - 1):
            for j in range(i + 1, len(games)):
                if (get_strat):
                    sij = (games[i][1] & games[j][1]).dag_size()
                    li = set(aig.get_bdd_latch_deps(games[i][1]))
                    lj = set(aig.get_bdd_latch_deps(games[j][1]))
                else:
                    sij = (games[i][2] & games[j][2]).dag_size()
                    li = set(aig.get_bdd_latch_deps(games[i][2]))
                    lj = set(aig.get_bdd_latch_deps(games[j][2]))
                cij = len(li & lj)
                nij = len(li | lj)
                triple_list.append((i, j, a * cij + b * nij + c * sij))
        # now we get the best pair according to the fij function
        (i, j, val) = max(triple_list, key=lambda x: x[2])
        log.DBG_MSG("We must reduce games " + str(i) + " and " + str(j))
        # we must reduce games i and j now
        if (get_strat):
            game = ConcGame(BDDAIG(aig).short_error(~(games[i][1] & games[j][1])),
                        use_trans=argv.use_trans)
        else:
            game = ConcGame(BDDAIG(aig).short_error(~(games[i][2] & games[j][2])),
                        use_trans=argv.use_trans)
        if (b_latchless and len(get_cinputs_of_game(games[i][0]) &
            get_cinputs_of_game(games[j][0])) == 0):
            w = games[i][1] & games[j][1]
            if w is None:
                return None
            s = None
            if (get_strat):
                s = games[i][2] & games[j][2]
        else:
            w = backward_safety_synth(game)
            if w is None:
                return None
            s = None
            if (get_strat):
                s = game.cpre(w, get_strat=True)
        games[i] = (game, s, w)
        games.pop(j)
        # lets simplify the transition relations
        # aig.restrict_latch_next_funs(s)
    return games[0][2]
