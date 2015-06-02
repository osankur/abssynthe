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

"""
TODO LIST 
1) For synthesis, the CPRE of the winning region is always computed
    although some realizability algorithms also do this computation
    This is redundant
   
   Also adapt the synthesis part to take into account a list of 
   winning strategies for subgames for the case of disjoint cont. inputs

2) How can we apply restrict on states? (rather than trans. functions?)


CHANGES

1) In comp. algorithms restricting the trans. functions by winning
quasi-strategies almost never reduce the BDD sizes. I commented this
in bdd_aig.short_error() function for the moment.

Romain's explanation: the  upre function already does restrict with ~dst_states
So the restrict in short_error is just redundant and could perhaps cause
unnecessary reordering

On genbuf9b3unrealy.aag, without restrict alg. 2 terminates in 5s, and with
restrict it takes ages (probably due to reordering)

2) The latch and input dependency functions have too much overhead.
I put a hash table on cudd_bdd.occ_sem() function
One could do the same for others (use profiling to detect these problems)

The bottleneck in Alg. 2 was this computation which was extremely redundant!
(e.g. on genbuf14c2unrealn.aag runing time was reduced from 1m to 12s.)

3) In Alg. 2 if cinputs (thus also latches) are independent we just need to intersect the winning
regions and strategies. No need to UPRE. DONE

4) Removed the unnecessary cpre in the last iteration of Alg.2

5) I got rid of the cpre computation in comp.1 it seems much faster
The same idea did a little worse for Alg.3, we're keeping the get_strat version
as default.

6) Modify Alg.2: if all BDD sizes exceed a given threshold finish them with
Alg.1. Didn't do anything with threshold 5000 or 8000
I think only the last BDD becomes big


Optimizations:
    - Choosing the subgame pairs that have the least joint cinputs were
      sometimes very beneficial:
      amba4b9y.aag went from 7.5s to 2.5s 
      however genbuf14c2unrealn.aag went from 13s to 17s

      Bad for opt:
        amba6c5y.aag 6s -> 30s
        amba6c4unrealy.aag 19s -> 33s

        cycle_sched_6: 9.5s -> 10.5s
            (noopt had more independent subgames)
        cycle_sched_7: 12.3 -> 13.5s
"""


import argparse
import log
from bdd_aig import BDDAIG
from algos import (
    backward_safety_synth,
    forward_safety_synth,
    forward_reachables,
    forward_solve
)
from bdd_games import (
    ConcGame,
    SymblicitGame,
)
from comp_algos import (
    decompose,
    comp_synth,
    comp_synth3,
    comp_synth4,
    subgame_mapper,
    subgame_reducer
)


EXIT_STATUS_REALIZABLE = 10
EXIT_STATUS_UNREALIZABLE = 20


def synth(argv):
    # parse the input spec
    aig = BDDAIG(aiger_file_name=argv.spec, intro_error_latch=True)
    return synth_from_spec(aig, argv)


def synth_from_spec(aig, argv):
    if argv.use_forward:
        game = ConcGame(aig,
                        use_trans=argv.use_trans,
                        opt_type=argv.opt_type)
        w = forward_solve(game)
        log.LOG_MSG("Realizable: " + str(w))
        exit(0)
    elif argv.use_reach:
        game = ConcGame(aig,
                        use_trans=argv.use_trans,
                        opt_type=argv.opt_type)
        w = forward_reachables(game)
        exit(0)
    # Explicit approach
    elif argv.use_symb:
        assert argv.out_file is None
        symgame = SymblicitGame(aig)
        w = forward_safety_synth(symgame)
    # Symbolic approach with compositional opts
    elif argv.decomp is not None:
        game_it = decompose(aig, argv)
        # if there was no decomposition possible then call simple
        # solver
        if game_it is None:
            argv.decomp = None
            return synth_from_spec(aig, argv)
        if argv.comp_algo == 1:
            # solve and aggregate sub-games
            (w, strat) = comp_synth(game_it,argv.get_strat)
        elif argv.comp_algo == 2:
            games_mapped = subgame_mapper(game_it, aig)
            if games_mapped is None:
                return False
            w = subgame_reducer(games_mapped, aig, argv)
        elif argv.comp_algo == 3:
            # solve games by up-down algo
            gen_game = ConcGame(aig, use_trans=argv.use_trans)
            w = comp_synth3(game_it, gen_game)
        elif argv.comp_algo == 4:
            # solve games by up-down algo
            gen_game = ConcGame(aig, use_trans=argv.use_trans)
            w = comp_synth4(game_it, gen_game)
        else:
            raise NotImplementedError()
    else:
        game = ConcGame(aig,
                        use_trans=argv.use_trans,
                        opt_type=argv.opt_type)
        w = backward_safety_synth(game)
    # final check
    if w is None:
        return False
    log.DBG_MSG("Win region bdd node count = " +
                str(w.dag_size()))
    # synthesis from the realizability analysis
    if w is not None:
        if argv.out_file is not None:
            log.DBG_MSG("Win region bdd node count = " +
                        str(w.dag_size()))
            c_input_info = []
            n_strategy = aig.cpre_bdd(w, get_strat=True)
            func_per_output = aig.extract_output_funs(n_strategy, care_set=w)
            if argv.only_transducer:
                for c in aig.iterate_controllable_inputs():
                    c_input_info.append((c.lit, c.name))
            for (c, func_bdd) in func_per_output.items():
                aig.input2and(c, aig.bdd2aig(func_bdd))
            if argv.only_transducer:
                aig.remove_outputs()
                for (l, n) in c_input_info:
                    aig.add_output(l, n)
            aig.write_spec(argv.out_file)
        return True
    else:
        return False


def main():
    parser = argparse.ArgumentParser(description="AIG Format Based Synth")
    parser.add_argument("spec", metavar="spec", type=str,
                        help="input specification in extended AIGER format")
    parser.add_argument("-r", "--reachability", action="store_true",
                        dest="use_reach", default=False,
                        help="Compute forward reach set")
    parser.add_argument("-f", "--forward", action="store_true",
                        dest="use_forward", default=False,
                        help="Forward alg.")
    parser.add_argument("-t", "--use_trans", action="store_true",
                        dest="use_trans", default=False,
                        help="Compute a transition relation")
    parser.add_argument("-s", "--use_symb", action="store_true",
                        dest="use_symb", default=False,
                        help="Use the symblicit forward approach")
    parser.add_argument("-d", "--decomp", dest="decomp", default=None,
                        type=str, help="Decomposition type", choices="12")
    parser.add_argument("-ca", "--comp_algo", dest="comp_algo", type=str,
                        default="1", choices="1234",
                        help="Choice of compositional algorithm")
    parser.add_argument("-opt", "--opt", dest="opt_type", type=str,
                        default="1", choices="12345",
                        help="Type of restrict optimization: (1) Nothing, (2)\
                        Local predecessor, (3) global coreachable set")
    parser.add_argument("-gs", "--strat", action="store_true", dest="get_strat",
                        default=False, help="")
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
    parser.add_argument("-ot", "--only_transducer", action="store_true",
                        dest="only_transducer", default=False,
                        help=("Output only the synth'd transducer (i.e. " +
                              "remove the error monitor logic)."))
    args = parser.parse_args()
    args.decomp = int(args.decomp) if args.decomp is not None else None
    args.comp_algo = int(args.comp_algo)
    args.opt_type = int(args.opt_type)
    # initialize the log verbose level
    log.parse_verbose_level(args.verbose_level)
    # realizability / synthesis
    is_realizable = synth(args)
    log.LOG_MSG("Realizable? " + str(bool(is_realizable)))
    exit([EXIT_STATUS_UNREALIZABLE, EXIT_STATUS_REALIZABLE][is_realizable])


if __name__ == "__main__":
    main()
