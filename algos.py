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

from abc import ABCMeta, abstractmethod
from itertools import imap
from utils import *
from functools import partial
import log
from cudd_bdd import BDD


# game templates for the algorithms implemented here, they all
# use only the functions provided here
class Game:
    __metaclass__ = ABCMeta

    @abstractmethod
    def error(self):
        pass

    @abstractmethod
    def init(self):
        pass


class VisitTracker:
    def __init__(self):
        self.attr = dict()

    def is_visited(self, v):
        return v in self.attr

    def is_in_attr(self, v):
        return v in self.attr and self.attr[v]

    def visit(self, v):
        self.attr[v] = False
        return self

    def mark_in_attr(self, v, b):
        self.attr[v] = b
        return self


class ForwardGame(Game):
    __metaclass__ = ABCMeta

    @abstractmethod
    def upost(self, src):
        pass

    @abstractmethod
    def cpost(self, src):
        pass

    @abstractmethod
    def is_env_state(self, state):
        pass

    def visit_tracker(self):
        return VisitTracker()


class BackwardGame(Game):
    __megaclass__ = ABCMeta

    @abstractmethod
    def upre(self, dst):
        pass

    @abstractmethod
    def cpre(self, dst, get_strat):
        pass


# OTFUR algo
def forward_safety_synth(game):
    assert isinstance(game, ForwardGame)
    init_state = game.init()
    error_states = game.error()
    tracker = game.visit_tracker()
    depend = dict()
    depend[init_state] = set()
    waiting = [(init_state, game.upost(init_state))] 
    while waiting and not tracker.is_in_attr(init_state):
        (s, sp_iter) = waiting.pop()
        try:
            sp = next(sp_iter)
        except StopIteration:
            continue  # nothing to do here
        # push the rest of the iterator back into the stack
        waiting.append((s, sp_iter))
        # process s, sp_iter
        if not tracker.is_visited(sp):
            tracker.visit(sp)
            tracker.mark_in_attr(
                sp, game.is_env_state(sp) and bool(sp & error_states))
            if sp in depend:
                depend[sp].add((s, iter([sp])))
            else:
                depend[sp] = set([(s, iter([sp]))])
            if tracker.is_in_attr(sp):
                waiting.append((s, iter([sp])))
            else:
                if game.is_env_state(sp):
                    waiting.append((sp, game.upost(sp)))
                else:
                    waiting.append((sp, game.cpost(sp)))
        else:
            local_lose = any(imap(tracker.is_in_attr, game.upost(s)))\
                if game.is_env_state(s)\
                else all(imap(tracker.is_in_attr, game.cpost(s)))
            if local_lose:
                tracker.mark_in_attr(s, True)
                waiting.extend(depend[s])
            if not tracker.is_in_attr(sp):
                depend[sp].add((s, sp))
    log.DBG_MSG("OTFUR, losing[init_state] = " +
                str(tracker.is_in_attr(init_state)))
    return None if tracker.is_in_attr(init_state) else True

# Classical backward fixpoint algo
def backward_safety_synth(game):
    assert isinstance(game, BackwardGame)
    init_state = game.init()
    error_states = game.error()
    log.DBG_MSG("Computing fixpoint of UPRE.")
    #latches = [l for l in game.aig.iterate_latches()]
    #for l in latches:
    #    print "Latch.next size: ", game.aig.lit2bdd(l.next).dag_size()
    #err_bdd = game.aig.lit2bdd(latches[-1].next)
    #if (err_bdd.dag_size()>4500):
    #    log.BDD_DMP(err_bdd, "error latch")
    win_region = ~fixpoint(
        error_states,
        fun=lambda x: x | game.upre(x),
        early_exit=lambda x: x & init_state
    )
    if not (win_region & init_state):
        return None
    else:
        return win_region

def forward_reachables(game):
    init_state = game.init()
    log.DBG_MSG("Computing forward reach.")
    reach_region = fixpoint(
        init_state,
        fun=lambda x: x | game.aig.post_bdd(x)
    )
    log.DBG_MSG("Forward Reach Set has size " + str(reach_region.dag_size()))
    return reach_region

def forward_solve(game):
    log.DBG_MSG("Solving forwards")
    init_state = game.init()
    error_states = game.error()
    # the onion rings during BFS traversal
    onionRings = [init_state]
    # union of the onion rings
    unionOfRings = init_state
    # the last ring of the BFS traversal - all that have been seen before
    front = onionRings[-1]
    while front != BDD.false():
        log.DBG_MSG("Forward step: " + str(len(onionRings)))
        oldfront = front
        front = game.aig.post_monolithic_bdd(oldfront) & ~unionOfRings
        onionRings.append(front)
        unionOfRings = unionOfRings | front
        if (front != BDD.false() and front & error_states == front):
            print "front <= error_states"
            return False
        elif (front & error_states != BDD.false()):
            log.DBG_MSG("\tReached error, going up backwards")
            # go back along the rings to do upre
            # always intersected with the i-th reachset
            berr = front & error_states
            # will be onionRings restricted to not yet losing states
            rem_states = [front & ~error_states]
            print "\t--front & ~error_states is empty: ", (rem_states[0] == BDD.false())
            print "\t--front & error_states is empty: ", (berr == BDD.false())
            for r in reversed(onionRings[:-1]):
                berr = game.aig.upre_bdd(berr) & r
                print "\t--berr is empty: ", (berr == BDD.false())
                rem_states.append(r & ~berr)
            if (berr != BDD.false()):
                return False
            onionRings = list(reversed(rem_states))
            unionOfRings = reduce(lambda x,y: x|y, onionRings)
            print "\tRefined onion ring size: " + str(len(onionRings))
            front = onionRings[-1]
            # At this point we have proved that no env strategy guarantees
            # reaching error in len(onionRings) steps
            # We also pruned the onion rings to the states not losing by such
            # strategies
    return True

