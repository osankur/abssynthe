# Swiss AbsSynthe
This is the _native_ version of the AbsSynthe tool, used to
synthesize controllers from succinct safety specifications.

* Version: 2.1
* Maintainer: Guillermo A. Perez (University of Antwerp)
* Contributors: Nicolas Basset, Romain Brenguier, Ocan Sankur, Jean-Francois Raskin 

The present fork contains the following extensions:
- If Environment is winning, a winning strategy is output for Environment if -o option is given.
- Best-effort strategies are computed for reachability objectives for Environment with the -b option.

## Building
We provide a building script for your convenience, but you may have to
customize it for your set up.

## Some dependencies:
The tool uses a simple version of the aiger library developed by the team of
Armin Biere (available at http://fmv.jku.at/aiger/). Specifically, we use
slightly modified versions of the aiger.c, aigtocnf.c, and aiger.h files.

We also make use of the cudd BDD library (version 2.5.1) included in the source
sub-folder.

# Citing

If you use AbsSynthe for your academic purposes, please cite the original
paper describing the tool:
```
@inproceedings{DBLP:journals/corr/BrenguierPRS14,
  author    = {Romain Brenguier and
               Guillermo A. P{\'{e}}rez and
               Jean{-}Fran{\c{c}}ois Raskin and
               Ocan Sankur},
  editor    = {Krishnendu Chatterjee and
               R{\"{u}}diger Ehlers and
               Susmit Jha},
  title     = {AbsSynthe: abstract synthesis from succinct safety specifications},
  booktitle = {Proceedings 3rd Workshop on Synthesis, {SYNT} 2014, Vienna, Austria,
               July 23-24, 2014},
  series    = {{EPTCS}},
  volume    = {157},
  pages     = {100--116},
  year      = {2014},
  url       = {https://doi.org/10.4204/EPTCS.157.11},
  doi       = {10.4204/EPTCS.157.11},
  timestamp = {Fri, 02 Nov 2018 09:30:18 +0100},
  biburl    = {https://dblp.org/rec/journals/corr/BrenguierPRS14.bib},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}
```

# Frequently asked questions
## What is the difference between the winning region and the inductive certificate that AbsSynthe can generate?
The idea behind the winning region that AbsSynthe can output is outlined in the rules of the synthesis-competition website (http://www.syntcomp.org/rules/).

For the winning region generation, I take a BDD representing the set of latch valuations (i.e. states) that are safe with respect to the specification. I then generate a new AIG file in which each latch becomes an input and the output of the encoded circuit has value 1 if and only if the given values for the latches correspond to a safe/winning state. Otherwise the value is 0. In AIGER terms, we started with a file whose input, latch, and output sets were I, L, O respectively. I create a new AIGER file with I', L', O' as new sets of inputs, latches, and outputs such that I' = L, O' = Win(I') and L' is empty.

For the inductive certificate we go beyond just safe states and want to capture all the controllable-input valuations that make it so that the uncontrollable-input valuation does not take the system outside of the safe/winning region. Again, starting from the BDD for the safe latch valuations, one can use the transition relation of the system and intersect it with the winning region so as to obtain precisely the desired transitions and build an AIG for it. Latches and inputs both become inputs in the new circuit and its output is 1 if and only if the given values correspond to an uncontrollable-input valuation and a controllable-input valuation so that, from the chosen latch valuation, we reach again a safe latch valuation. In AIGER terms, we create a file with I', L', O' as new sets of inputs, latches, and outputs such that I' = I U L, O' = T(L,I,L'') ^ Win(L''), and L' is empty.

# Changelog

## The `reach_synt` branch: Best-Effort Reachability
The current branch adds the following features:
- The new -b option solves the best-effort reachability problem: it computes the winning region W_0 for environment (thus with reachability objective),
but also the set of cooperative states C_0 from which some pair of controllable and uncontrollable input leads to the winning region W_0. The attractor of this larger set W_0 union C_0 is computed and called W_1, and another layer of cooperative states C_1 (which can reach W_1 in one step) is computed. This is repeated  until all coreachable states are covered. 
- The -o option now outputs the full circuit controlled by the winning strategy, whether it is player 1 or player 2. The file contains the controlled circuit with additional outputs:
    - An output called `_attractor_` represents the union of W_i (a state sets this output to 1 iff it belongs to this union)
    - An output called `_cooperation_` is the union of C_i
    - A list of outputs `_pre0_`, `_pre1_`, etc. are the backwards reachability layers (`_pre0_` is `err`, `_pre1_` is its predecessors etc.)

## UPDATES v2.1
Besides bug fixing, this version includes options for
* a forced reordering just before generating the output circuit (so as
  to minimize the size of the BDDs on which the circuit is based)
* a way of reducing the number of subgames for the compositional algorithms
  based on the idea that subgames that do not depend on the same variables
  may be easy to solve but do not give much information; hence, we combine
  them into more complicated games which are (hopefully) more instructive
  regarding the realizability of the global game
* generation of the winning refion being inductively invariant in AIGER
  (previously available only in QDIMACS format)

## UPDATES v2.0
For this new version of Swiss AbsSynthe we have implemented a new abstraction
algorithm and one more compositional algorithm.

Additionally, there are new options to output
1. an aag version of the winning region if the given input spec is realizable
   and 
2. a QDIMACS certificate of the winning region being inductively invariant,
   that is there is some way to choose controllable inputs -- which depends on
   the latches and uncontrollable inputs -- which allows the controller to
   stay in the winning region if it started from the winning region. The
   latter can be fed into a QBF solver to obtain Skolem functions: a strategy.
