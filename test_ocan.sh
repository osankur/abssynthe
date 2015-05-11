#!/bin/bash

# This is a benchmark framework that may be useful for evaluating
# synthesis tools developed for SyntComp.
#
# Version: 1.0.1
# Created by Robert Koenighofer, robert.koenighofer@iaik.tugraz.at
# Comments/edits by Swen Jacobs, swen.jacobs@iaik.tugraz.at

# This directory:
DIR=`dirname $0`/

# Time limit in seconds:
TIME_LIMIT=500
# Memory limit in kB:
MEMORY_LIMIT=2000000

# Maybe change the following line to point to GNU time:
GNU_TIME="time"
MODEL_CHECKER="$DIR/../blimc/blimc"
SYNT_CHECKER="$DIR/../aiger/syntactic_checker.py"

# The directory where the benchmarks are located:
BM_DIR="${DIR}/../bench-syntcomp14/"

REAL=10
UNREAL=20

# The benchmarks to be used.
# The files have to be located in ${BM_DIR}.
FILES=(
#mult_bool_matrix_2_2_10
#mult_bool_matrix_2_2_11
#mult_bool_matrix_2_2_12
#mult_bool_matrix_2_2_13
#mult_bool_matrix_2_2_14
#mult_bool_matrix_2_2_15
#mult_bool_matrix_2_2_16
#mult_bool_matrix_2_2_17
#mult_bool_matrix_2_2_18
#mult_bool_matrix_2_2_19
#mult_bool_matrix_2_2_20
#mult_bool_matrix_2_2_21
#mult_bool_matrix_2_2_22
#mult_bool_matrix_2_2_23
#mult_bool_matrix_2_2_24
#mult_bool_matrix_2_2_25
#mult_bool_matrix_2_2_26
#mult_bool_matrix_2_2_27
#mult_bool_matrix_2_2_28
#mult_bool_matrix_2_2_29
#mult_bool_matrix_2_2_2
#mult_bool_matrix_2_2_30
#mult_bool_matrix_2_2_3
#mult_bool_matrix_2_2_4
#mult_bool_matrix_2_2_5
#mult_bool_matrix_2_2_6
#mult_bool_matrix_2_2_7
#mult_bool_matrix_2_2_8
#mult_bool_matrix_2_2_9
#mult_bool_matrix_2_3_10
#mult_bool_matrix_2_3_11
#mult_bool_matrix_2_3_12
#mult_bool_matrix_2_3_13
#mult_bool_matrix_2_3_14
#mult_bool_matrix_2_3_15
#mult_bool_matrix_2_3_16
#mult_bool_matrix_2_3_17
#mult_bool_matrix_2_3_18
#mult_bool_matrix_2_3_19
#mult_bool_matrix_2_3_20
#mult_bool_matrix_2_3_21
#mult_bool_matrix_2_3_22
#mult_bool_matrix_2_3_23
#mult_bool_matrix_2_3_24
#mult_bool_matrix_2_3_25
#mult_bool_matrix_2_3_26
#mult_bool_matrix_2_3_27
#mult_bool_matrix_2_3_28
#mult_bool_matrix_2_3_29
#mult_bool_matrix_2_3_2
#mult_bool_matrix_2_3_30
#mult_bool_matrix_2_3_3
#mult_bool_matrix_2_3_4
#mult_bool_matrix_2_3_5
#mult_bool_matrix_2_3_6
#mult_bool_matrix_2_3_7
#mult_bool_matrix_2_3_8
#mult_bool_matrix_2_3_9
#mult_bool_matrix_2
#mult_bool_matrix_3_3_2
#mult_bool_matrix_3_3_3
#mult_bool_matrix_3_3_4
#mult_bool_matrix_3_3_5
#mult_bool_matrix_3_4_2
#mult_bool_matrix_3_4_3
#mult_bool_matrix_3_4_4
#mult_bool_matrix_3_4_5
#mult_bool_matrix_3_5_5
#mult_bool_matrix_3
#mult_bool_matrix_4_4_4
#mult_bool_matrix_4_4_5
#mult_bool_matrix_4_5_5
#mult_bool_matrix_4
#mult_bool_matrix_5_5_5
#mult_bool_matrix_5
#mult_bool_matrix_6_6_6
#mult_bool_matrix_6_6_7
#mult_bool_matrix_6_6_8
#mult_bool_matrix_6_7_10
#mult_bool_matrix_6_7_7
#mult_bool_matrix_6_7_8
#mult_bool_matrix_6_7_9
#mult_bool_matrix_6_8_10
#mult_bool_matrix_6_8_8
#mult_bool_matrix_6_8_9
#mult_bool_matrix_6_9_10
#mult_bool_matrix_6
#mult_bool_matrix_7_10_10
#mult_bool_matrix_7_6_10
#mult_bool_matrix_7_6_6
#mult_bool_matrix_7_6_8
#mult_bool_matrix_7_6_9
#mult_bool_matrix_7_7_10
#mult_bool_matrix_7_7_7
#mult_bool_matrix_7_7_8
#mult_bool_matrix_7_7_9
#mult_bool_matrix_7_8_10
#mult_bool_matrix_7_8_8
#mult_bool_matrix_7_8_9
#mult_bool_matrix_7_9_10
#mult_bool_matrix_7_9_9
#mult_bool_matrix_7
#mult_bool_matrix_8_10_10
#mult_bool_matrix_8_6_10
#mult_bool_matrix_8_6_6
#mult_bool_matrix_8_6_7
#mult_bool_matrix_8_6_9
#mult_bool_matrix_8_7_10
#mult_bool_matrix_8_7_7
#mult_bool_matrix_8_7_9
#mult_bool_matrix_8_8_10
#mult_bool_matrix_8_8_8
#mult_bool_matrix_8_8_9
#mult_bool_matrix_8_9_10
#mult_bool_matrix_8_9_9
#mult_bool_matrix_9_10_10
#mult_bool_matrix_9_10_11
#mult_bool_matrix_9_10_12
#mult_bool_matrix_9_10_13
#mult_bool_matrix_9_10_14
#mult_bool_matrix_9_11_13
#mult_bool_matrix_9_12_13
#mult_bool_matrix_9_9_9
#mult_bool_matrix_10_10_11
#mult_bool_matrix_10_10_12
#mult_bool_matrix_10_10_13
#mult_bool_matrix_10_11_11
#mult_bool_matrix_10_11_12
#mult_bool_matrix_10_11_13
#mult_bool_matrix_10_12_12
#mult_bool_matrix_10_12_13
#mult_bool_matrix_10_13_13
#mult_bool_matrix_11_11_11
#mult_bool_matrix_11_11_12
#mult_bool_matrix_11_11_13
#mult_bool_matrix_11_12_12
#mult_bool_matrix_11_12_13
#mult_bool_matrix_11_13_13
#mult_bool_matrix_12_12_12
#mult_bool_matrix_12_12_13
#mult_bool_matrix_12_13_13
#mult_bool_matrix_13_13_13
#mult_bool_matrix_14_14_14
#mult_bool_matrix_15_15_15
#mult_bool_matrix_16_16_16
#mult_bool_matrix_17_17_17
#mult_bool_matrix_18_18_18
#mult_bool_matrix_19_19_19
#mult_bool_matrix_20_20_20
#mult_bool_matrix_21_21_21
cycle_sched_2 $REAL
cycle_sched_3 $REAL
cycle_sched_4 $REAL
cycle_sched_5 $REAL
cycle_sched_6 $REAL
cycle_sched_7 $REAL
cycle_sched_8 $REAL
cycle_sched_9 $REAL
cycle_sched_10 $REAL
cycle_sched_11 $REAL
cycle_sched_12 $REAL
cycle_sched_13 $REAL
#cycle_sched_16 $REAL
#cycle_sched_17 $REAL
#cycle_sched_18 $REAL
#cycle_sched_19 $REAL
#cycle_sched_20 $REAL
#cycle_sched_21 $REAL
#cycle_sched_22 $REAL
#cycle_sched_23 $REAL
#cycle_sched_24 $REAL
#cycle_sched_25 $REAL
#cycle_sched_26 $REAL
amba2b8unrealn    $UNREAL
amba2b8unrealy    $UNREAL
amba2b9n    $REAL
amba2b9y    $REAL
amba2c6unrealn    $UNREAL
amba2c6unrealy    $UNREAL
amba2c7n    $REAL
amba2c7y    $REAL
amba2f8unrealn    $UNREAL
amba2f8unrealy    $UNREAL
amba2f9n    $REAL
amba2f9y    $REAL
amba3b4unrealn    $UNREAL
amba3b4unrealy    $UNREAL
amba3b5n    $REAL
amba3b5y    $REAL
amba3c4unrealn    $UNREAL
amba3c4unrealy    $UNREAL
amba3c5n    $REAL
amba3c5y    $REAL
amba3f8unrealn    $UNREAL
amba3f8unrealy    $UNREAL
amba3f9n    $REAL
amba3f9y    $REAL
amba4b8unrealn    $UNREAL
amba4b8unrealy    $UNREAL
amba4b9n    $REAL
amba4b9y    $REAL
amba4c6unrealn    $UNREAL
amba4c6unrealy    $UNREAL
amba4c7n    $REAL
amba4c7y    $REAL
amba4f24unrealn    $UNREAL
amba4f24unrealy    $UNREAL
amba4f25n    $REAL
amba4f25y    $REAL
amba5b4unrealn    $UNREAL
amba5b4unrealy    $UNREAL
amba5b5n    $REAL
amba5b5y    $REAL
amba5c4unrealn    $UNREAL
amba5c4unrealy    $UNREAL
amba5c5n    $REAL
amba5c5y    $REAL
demo-v2_2_UNREAL    $UNREAL
demo-v2_5_UNREAL    $UNREAL
demo-v3_2_REAL    $REAL
demo-v3_5_REAL    $REAL
demo-v4_2_UNREAL    $UNREAL
demo-v4_5_REAL    $REAL
demo-v5_2_REAL    $REAL
demo-v5_5_REAL    $REAL
demo-v6_2_UNREAL    $UNREAL
demo-v6_5_REAL    $REAL
factory_assembly_3x3_1_1errors    $UNREAL
factory_assembly_4x3_1_1errors    $REAL
factory_assembly_5x3_1_0errors    $REAL
factory_assembly_5x3_1_4errors    $REAL
genbuf10b3unrealn    $UNREAL
genbuf10b3unrealy    $UNREAL
genbuf10b4n    $REAL
genbuf10b4y    $REAL
genbuf10c2unrealn    $UNREAL
genbuf10c2unrealy    $UNREAL
genbuf10c3n    $REAL
genbuf10c3y    $REAL
genbuf10f10n    $REAL
genbuf10f10y    $REAL
genbuf10f9unrealn    $UNREAL
genbuf10f9unrealy    $UNREAL
genbuf11b3unrealn    $UNREAL
genbuf11b3unrealy    $UNREAL
genbuf11b4n    $REAL
genbuf11b4y    $REAL
genbuf11c2unrealn    $UNREAL
genbuf11c2unrealy    $UNREAL
genbuf11c3n    $REAL
genbuf11c3y    $REAL
genbuf11f10unrealn    $UNREAL
genbuf11f10unrealy    $UNREAL
genbuf11f11n    $REAL
genbuf11f11y    $REAL
genbuf2b3unrealy    $UNREAL
genbuf2b4n    $REAL
genbuf2b4y    $REAL
genbuf2c2unrealn    $UNREAL
genbuf2c2unrealy    $UNREAL
genbuf2c3n    $REAL
genbuf2c3y    $REAL
genbuf2f3unrealn    $UNREAL
genbuf2f3unrealy    $UNREAL
genbuf2f4n    $REAL
genbuf2f4y    $REAL
genbuf3b3unrealn    $UNREAL
genbuf3b3unrealy    $UNREAL
genbuf3b4n    $REAL
genbuf3b4y    $REAL
genbuf3c2unrealn    $UNREAL
genbuf3c2unrealy    $UNREAL
genbuf3c3n    $REAL
genbuf3c3y    $REAL
genbuf3f3unrealn    $UNREAL
genbuf3f3unrealy    $UNREAL
genbuf3f4n    $REAL
genbuf3f4y    $REAL
genbuf4b3unrealn    $UNREAL
genbuf4b3unrealy    $UNREAL
genbuf4b4n    $REAL
genbuf4b4y    $REAL
genbuf4c2unrealn    $UNREAL
genbuf4c2unrealy    $UNREAL
genbuf4c3n    $REAL
genbuf4c3y    $REAL
genbuf4f3unrealn    $UNREAL
genbuf4f3unrealy    $UNREAL
genbuf4f4n    $REAL
genbuf4f4y    $REAL
genbuf5b3unrealn    $UNREAL
genbuf5b3unrealy    $UNREAL
genbuf5b4n    $REAL
genbuf5b4y    $REAL
genbuf5c2unrealn    $UNREAL
genbuf5c2unrealy    $UNREAL
genbuf5c3n    $REAL
genbuf5c3y    $REAL
genbuf5f4unrealn    $UNREAL
genbuf5f4unrealy    $UNREAL
genbuf5f5n    $REAL
genbuf5f5y    $REAL
genbuf6b3unrealn    $UNREAL
genbuf6b3unrealy    $UNREAL
genbuf6b4n    $REAL
genbuf6b4y    $REAL
genbuf6c2unrealn    $UNREAL
genbuf6c2unrealy    $UNREAL
gb_s2_r2_comp1_UNREAL   $UNREAL
gb_s2_r2_comp2_UNREAL   $UNREAL
load_full_2_comp1_UNREAL   $UNREAL
load_full_2_comp2_REAL   $REAL
load_full_2_comp3_REAL   $REAL
load_full_3_comp1_UNREAL   $UNREAL
load_2c_comp_comp1_REAL   $REAL
load_2c_comp_comp2_REAL   $REAL
load_2c_comp_comp3_REAL   $REAL
gb_s2_r7_comp7_REAL
gb_s2_r7_comp1_UNREAL
gb_s2_r7_comp1_UNREAL
gb_s2_r3_comp1_UNREAL
gb_s2_r3_comp1_UNREAL
gb_s2_r3_comp2_UNREAL
gb_s2_r3_comp2_UNREAL
gb_s2_r4_comp1_UNREAL
gb_s2_r4_comp1_UNREAL
gb_s2_r4_comp2_REAL
gb_s2_r4_comp2_REAL
gb_s2_r6_comp1_UNREAL
gb_s2_r6_comp1_UNREAL
gb_s2_r6_comp2_UNREAL
gb_s2_r6_comp2_UNREAL
)

CALL_SYNTH_TOOL="./start abssynthe.py -v L -ca 1 -d 1 $@ "
TIMESTAMP=`date +%s`
RES_TXT_FILE="${DIR}tests/ca1_restrict_${TIMESTAMP}.txt"
RES_DIR="${DIR}tests/tmp_${TIMESTAMP}/"
mkdir -p "${DIR}tests/"
mkdir -p ${RES_DIR}

ulimit -m ${MEMORY_LIMIT} -v ${MEMORY_LIMIT} -t ${TIME_LIMIT}
for element in $(seq 0 2 $((${#FILES[@]} - 1)))
do
     file_name=${FILES[$element]}
     infile_path=${BM_DIR}${file_name}.aag
     outfile_path=${RES_DIR}${file_name}_synth.aag
     correct_real=${FILES[$element+1]}
     echo "Synthesizing ${file_name}.aag ..."
     echo "=====================  $file_name.aag =====================" 1>> $RES_TXT_FILE

     #------------------------------------------------------------------------------
     # BEGIN execution of synthesis tool
     echo " Running the synthesizer ... "
     ${GNU_TIME} --output=${RES_TXT_FILE} -a -f "Synthesis time: %e sec (Real time) / %U sec (User CPU time)" ${CALL_SYNTH_TOOL} $infile_path >> ${RES_TXT_FILE}
     #"-o" $outfile_path "-ot" >> ${RES_TXT_FILE}
     exit_code=$?
     echo "  Done running the synthesizer. "
     # END execution of synthesis tool

     if [[ $exit_code == 137 ]];
     then
         echo "  Timeout!"
         echo "Timeout: 1" 1>> $RES_TXT_FILE
         continue
     else
         echo "Timeout: 0" 1>> $RES_TXT_FILE
     fi

     if [[ $exit_code != $REAL && $exit_code != $UNREAL ]];
     then
         echo "  Strange exit code: $exit_code (crash or out-of-memory)!"
         echo "Crash or out-of-mem: 1 (Exit code: $exit_code)" 1>> $RES_TXT_FILE
         continue
     else
         echo "Crash or out-of-mem: 0" 1>> $RES_TXT_FILE
     fi

     #------------------------------------------------------------------------------
     # BEGIN analyze realizability verdict
     if [[ $exit_code == $REAL && $correct_real == $UNREAL ]];
     then
         echo "  ERROR: Tool reported 'realizable' for an unrealizable spec!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
         echo "Realizability correct: 0 (tool reported 'realizable' instead of 'unrealizable')" 1>> $RES_TXT_FILE
         continue
     fi
     if [[ $exit_code == $UNREAL && $correct_real == $REAL ]];
     then
         echo "  ERROR: Tool reported 'unrealizable' for a realizable spec!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
         echo "Realizability correct: 0 (tool reported 'unrealizable' instead of 'realizable')" 1>> $RES_TXT_FILE
         continue
     fi
     if [[ $exit_code == $UNREAL ]];
     then
         echo "  The spec has been correctly identified as 'unrealizable'."
         echo "Realizability correct: 1 (unrealizable)" 1>> $RES_TXT_FILE
     else
         echo "  The spec has been correctly identified as 'realizable'."
         echo "Realizability correct: 1 (realizable)" 1>> $RES_TXT_FILE
#
#         # END analyze realizability verdict
#
#         #------------------------------------------------------------------------------
#         # BEGIN syntactic check
#         echo " Checking the synthesis result syntactically ... "
#         if [ -f $outfile_path ];
#         then
#             echo "  Output file has been created."
#             python $SYNT_CHECKER $infile_path $outfile_path
#             exit_code=$?
#             if [[ $exit_code == 0 ]];
#             then
#               echo "  Output file is OK syntactically."
#               echo "Output file OK: 1" 1>> $RES_TXT_FILE
#             else
#               echo "  Output file is NOT OK syntactically."
#               echo "Output file OK: 0" 1>> $RES_TXT_FILE
#             fi
#         else
#             echo "  Output file has NOT been created!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
#             echo "Output file OK: 0 (no output file created)" 1>> $RES_TXT_FILE
#             continue
#         fi
#         # TODO: perform syntactic check here.
#         # END syntactic check
#
#         #------------------------------------------------------------------------------
#         # BEGIN model checking
#         echo -n " Model checking the synthesis result ... "
#         ${GNU_TIME} --output=${RES_TXT_FILE} -a -f "Model-checking time: %e sec (Real time) / %U sec (User CPU time)" $MODEL_CHECKER $outfile_path > /dev/null 2>&1
#         check_res=$?
#         echo " done. "
#         if [[ $check_res == 20 ]];
#         then
#             echo "  Model-checking was successful."
#             echo "Model-checking: 1" 1>> $RES_TXT_FILE
#         else
#             echo "  Model-checking the resulting circuit failed!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
#             echo "Model-checking: 0 (exit code: $check_res)" 1>> $RES_TXT_FILE
#         fi
#         # END end checking
#
#         #------------------------------------------------------------------------------
         # BEGIN determining circuit size
#         aig_header_in=$(head -n 1 $infile_path)
#         aig_header_out=$(head -n 1 $outfile_path)
#         echo "Raw AIGER input size: $aig_header_in" 1>> $RES_TXT_FILE
#         echo "Raw AIGER output size: $aig_header_out" 1>> $RES_TXT_FILE
#         # START ABC optimization to compare sizes
#         ../aiger/aigtoaig $outfile_path "${outfile_path}.aig"
#         ../ABC/abc -c "read_aiger ${outfile_path}.aig; strash; refactor; rewrite; dfraig; scleanup; rewrite; dfraig; write_aiger -s ${outfile_path}_opt.aig"
#         ../aiger/aigtoaig "${outfile_path}_opt.aig" "${outfile_path}_opt.aag"
#         aig_header_opt=$(head -n 1 "${outfile_path}_opt.aag")
#         echo "Raw AIGER opt size: $aig_header_opt" 1>> $RES_TXT_FILE
#         # END determining circuit size           
     fi
done
