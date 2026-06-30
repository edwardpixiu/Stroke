#/bin/tcsh
#
#
# The script is for multiple runs data GLM regression
#

if ( $#argv < 1 ) then
	echo "[Error]: The scirpt input mustify the following format: <multi-runs .scale data> <TR> <Duration>..."
	
	echo "[Info]: You can input the multi-runs .scale data like: tcsh <script> pbxx.fMRI.runxx.scale+tlrc. ... pbxx.fMRI.runxx.scale+tlrc"

	exit 1
endif 


set afni_dir = ./Afni

set env_cur = `pwd`

set concat_file = "${env_cur}/Func_Analyze_Script/concat_volreg.py"

set time_generator = "${env_cur}/Func_Analyze_Script/time_series.py"

mkdir Glm
set glm = ./Glm

set prefix = pb11.funcfMRI.deob.scale

set runs_scale_data = ()
@ use = $#argv - 2
foreach f ( $argv[1-$use] )
	set parts = ( $f:as/+/\ / )
	echo "[DEBUG]: parts1 = ${parts}[1]"
	echo "[DEBUG]: parts2 = ${parts}[2]"
	if ( "$f:e" == "HEAD" || "$f:e" == "BRIK" || $parts[2] == "tlrc." ) then
		set runs_scale_data = ( $runs_scale_data "$f" )
	endif
end

set runs_num = $#runs_scale_data

@ rem = $runs_num % 2

if ( $rem != 0 ) then
	echo "[Error]: Input file amount must be even."
	exit 1
endif

@ stims_num = $runs_num / 2 

@ idx1 = $#argv - 1
set TR = $argv[$idx1]

set duration = $argv[$#argv]

echo "[DEBUG]: runs_num:$runs_num"

set concat_cmd = "python $concat_file"

@ run = 0

set run_dims = ()

while ( $run < $runs_num )

	@ run_id = $run + 1

	set run_label = `printf "%02d" $run_id`

	set current_scale_data = "${afni_dir}/${prefix}.run${run_label}+tlrc"
	
	set dims_file = "${afni_dir}/dfile.run${run_label}.6dimensions.1D"

	echo "[DEBUG]: Current recursive data: ${current_scale_data}, ${dims_file}"

	if ( -e "${current_scale_data}.HEAD" && -r "${current_scale_data}.BRIK" ) then
		echo "[DEBUG]: The file is existed! ${current_scale_data}"
	else
		echo "[DEBUG]: Missing the file ..."
	endif
	
	echo "[Info]: Start <concat_volreg.py> ..."
	
	set run_dims = ( $run_dims -V "$dims_file" )


	@ run++

end

echo $run_dims

set allvol = dfileAllvol.1D

set concat_cmd = "$concat_cmd $run_dims -O ${glm}/$allvol"

eval $concat_cmd

# set allvol = dfileAllvol.1D

# Demeans
#

set demeans_file = "motion_demean.1D"

echo "[Info]: Start time-sequence volreg params demeaning ..."

1d_tool.py -infile $glm/${allvol} -set_nruns $runs_num -demean -write $glm/${demeans_file}

echo "[Info]: Finish time-sequence volreg params demeaning ... -> $glm/${demeans_file}"

# Derivative
#

set derivative_file = "motion_deriv.1D"

echo "[Info]: Start time-sequence volreg params demeaning && derivative ..."

1d_tool.py -infile $glm/${allvol} -set_nruns $runs_num -demean -derivative -write $glm/${derivative_file}

echo "[Info]: Finish time-sequence volreg params demeaning && derivative ... -> $glm/${derivative_file}"

# Split into runs
#

set mot_demeans = "mot.demeans"

echo "[Info]: Splitting motion_demeans.1D into individual run ..."

1d_tool.py -infile $glm/$demeans_file -set_nruns $runs_num -split_into_pad_runs $glm/$mot_demeans

echo "[Info]: Finish motion-demeans.1D splitting ... -> $glm/$mot_demeans"

# Filter demeaned volreg parameters
#

echo "[Info]: Starting <Filter demean>"

1d_tool.py -infile $glm/${allvol} -set_nruns $runs_num -show_censor_count \
	-censor_prev_TR -censor_motion 0.3 $glm/motion_filter

echo "[Info]: Finish <filter demean>"

# State censored Runs
#

echo "[Info]: Starting state censored runs ..."

1d_tool.py -infile $glm/motion_filter_censor.1D -show_trs_uncensored encoded

# Generate the Stimulations-time series file
set idx = 1
while ( $idx <= $stims_num )
	set time_simulations = $glm/"stims_time".${idx}.txt
	python $time_generator -R $runs_num -TR $TR -D $duration -O $time_simulations

# GLM
#
set deri = `awk "BEGIN {print $TR * $stims_num * 2}"`
echo "[DEBUG]: deri: $deri"
set bricks = `awk "BEGIN {print $duration / $deri}"`

set rbricks = `awk "BEGIN {print ${bricks}-2}"`
set period = `awk "BEGIN {print ${TR} * ${rbricks}}"`


set ortvec_cmd = ""
set run = 1

while ( $run <= $runs_num )
	set run_str = `printf "%02d" $run`
	set ortvec_cmd = "${ortvec_cmd} -ortvec $glm/${mot_demeans}.r${run_str}.1D Run_${run_str}"
	@ run++
end

set input_cmd = ()
foreach fmri ($runs_scale_data)
	set input_cmd = ( $input_cmd "$fmri" )
end

echo "[DEBUG]: input cmd = $input_cmd"
echo "[DEBUG]: Number of input files = $#input_cmd"

3dDeconvolve -input $input_cmd \
	-censor $glm/motion_filter_censor.1D \
	$ortvec_cmd \
	-polort a \
	-local_times \
	-num_stimts 1 \
	-stim_times 1 ${env_cur}/$time_simulations 'BLOCK('$period',1)' \
	-stim_label 1 MI \
	-fout -tout -x1D $glm/X.mat.1D -xjpeg $glm/X.jpg \
	-x1D_uncensored $glm/X.nocensor.x.mat.1D \
	-errts $glm/errts.stims \
	-bucket $glm/X.stats
