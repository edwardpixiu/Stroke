#!/bin/tcsh
#
#
# Creating a independent workspace for AFNI part
#
# first version is writing by edward huang on 2026/06/23
#

if ( $#argv < 3 ) then
	echo "[Error]: Usage: tcsh fMRI_AFNI_Pipeline.tcsh <unwrapped_epi_fsl.nii.gz> <runs> <T1_anat.nii.gz>"
	exit 1
endif

mkdir Afni
cd ./Afni

set unwrapped_epi = $1

set MNI = /data/software/afni/MNI152_2009_template.nii.gz

# Deoblique

set fmri_00_name = "funcfMRI.deob.raw"
3dWarp -deoblique -prefix pb00.${fmri_00_name} $unwrapped_epi

# Seperately process

set tcat_num = 2
set fmri_01_name = pb01.${fmri_00_name:r}.tcat

set nruns = $2

set volumes = `3dinfo -nt pb00.$fmri_00_name+orig.`

# echo "[DEBUG]: ${fmri_00_name}+orig."

set T1_anat = "T1_anat"
set T1_raw = $3
3dSkullStrip -prefix $T1_anat -input $T1_raw

echo "[Info]: T1 anatomy image skullstriping..."
3dinfo $T1_anat

set align_T1_2MNI = align.T1.2MNI152
set T1_2MNI = Temp.T1.2MNI152.rm

echo "[Info]: Registering T1 anatomy image into MNI152 space ..."
3dAllineate -base $MNI -source $T1_anat+orig. -float -cmass -cost lpa \
	-interp cubic -twopass -1Dmatrix_save $align_T1_2MNI -autoweight -source_automask -prefix ${T1_2MNI}

@ run_len = $volumes / $nruns

@ r = 0

echo "[Info]: Starting process ..."

while ( $r < $nruns )
	

	@ id_start = $r * $run_len + $tcat_num
	
	@ id_end = $r + 1 
	@ id_end = $id_end * $run_len - 1

	@ run_id = $r + 1

	set run_label = `printf "%02d" $run_id`

	echo "[Info]: Creating run${run_label}_part: volumes ${id_start}...${id_end}"
	
	echo "[Info]: Tcat: pb00.${fmri_00_name}+orig. -> ${fmri_01_name}.run${run_label}.orig"

	3dTcat \
		-prefix ${fmri_01_name}.run${run_label} \
			pb00.${fmri_00_name}+orig.'['${id_start}'..'${id_end}']'


	set fmri_02_name = pb02.${fmri_00_name:r}.tshift
	
	echo "[Info]: Time Aligning: ${fmri_01_name}.run${run_label}+orig. -> ${fmri_02_name}.run${run_label}+orig."

	3dTshift \
		-tzero 0 -quintic -prefix ${fmri_02_name}.run${run_label} \
			${fmri_01_name}.run${run_label}+orig.

	# Automask -> Toutcount -> Reference Pickup -> Skullstrip
	#
	# set fmri_03_name = pb03.${fmri_00_name:r}.Skullstrip

	# echo "[Info]: Skullstrip... ${fmri_02_name}.run${run_label}+orig. -> ${fmri_03_name}.run${run_label}+orig."

	# 3dSkullStrip \
		#	-prefix ${fmri_03_name}.run${run_label} -input ${fmri_02_name}.run${run_label}+orig.

	set fmri_03_name = pb03.${fmri_00_name:r}.mask

	echo "[Info]: Calculating whole-brain mask... ${fmri_02_name}.run${run_label}+orig. -> ${fmri_03_name}.run${run_label}+orig."

	3dAutomask \
		-prefix ${fmri_03_name}.run${run_label} ${fmri_02_name}.run${run_label}+orig.

	set min_outliers_allTRs = "min.outliers.allTRs.${run_label}.1D"
	
	echo "[Info]: Extracting outliers... --> ${min_outliers_allTRs}"

	3dToutcount -mask ${fmri_03_name}.run${run_label}+orig. -fraction -polort 2 -legendre ${fmri_02_name}.run${run_label}+orig. > $min_outliers_allTRs

	set a = `awk 'BEGIN {min=999; idx=-1} \
		{if ($1 < min) {min=$1; idx=NR-1}} \
			END {print idx}' $min_outliers_allTRs`

	set fmri_04_name = pb04.${fmri_00_name:r}.ref

	echo "[Info]: Extracting reference slice... -> ${fmri_04_name}.run${run_label}+orig."

	3dbucket -prefix $fmri_04_name.run${run_label} ${fmri_02_name}.run${run_label}+orig."[$a]"

	set fmri_05_name = pb05.${fmri_00_name:r}.volreg.rm 

	set align_matrix = align.${fmri_00_name:r}.run${run_label}.2.ref

	set align_1D_file = dfile.run${run_label}.6dimensions.1D
	
	echo "[Info]: Starting head motion regress to reference slice ..."

	# Head motion Volreg, the volreg represent of single-run fmri to its ref
	#
	3dvolreg -verbose -zpad 5 -base ${fmri_04_name}.run${run_label}+orig. -1Dfile ${align_1D_file} -prefix ${fmri_05_name}.run${run_label} \
		-cubic -1Dmatrix_save ${align_matrix} ${fmri_02_name}.run${run_label}+orig.

	echo "[Info]: Finish head motion volreg to the reference slice ..."
	
	echo "[Info]: Starting Skullstrip ..."
	
	set fmri_06_name = pb06.${fmri_00_name:r}.SS

	3dcalc -a ${fmri_02_name}.run${run_label}+orig. -b ${fmri_03_name}.run${run_label}+orig. -expr 'a*b' -prefix ${fmri_06_name}.run${run_label}

	# Align ref -> T1_anat: align.ref.2.T1.1Dmatrix
	# Align T1_anat -> MNI152: align.T1.2.MNI.1Dmatrix
	#
	
	set align_ref2T1 = align.ref2T1.run${run_label}
	set fmri_07_name = pb07.${fmri_00_name:r}.ref2T1.rm
	3dAllineate -base $T1_anat+orig. -source ${fmri_04_name}.run${run_label}+orig. -float -1Dmatrix_save $align_ref2T1 -cost lpa \
		-interp linear -cmass -EPI -twopass -source_automask -autoweight -prefix ${fmri_07_name}.run${run_label}
	
	set align_epi2MNI = align.epi2MNI.run${run_label}.1D
	echo "[Info]: Calculating forward registeration matrix -> ${align_epi2MNI}..."
	cat_matvec -ONELINE ${align_matrix}.* ${align_ref2T1}.* ${align_T1_2MNI}.* > ${align_epi2MNI}

	echo "[Info]: Start forward register ..."
	set fmri_08_name = pb08.${fmri_00_name:r}.epi2MNI
	3dAllineate -master $MNI -source ${fmri_06_name}.run${run_label}+orig. -float -cost lpa -final linear \
		-1Dmatrix_apply ${align_epi2MNI} -cmass -EPI -twopass -source_automask+5 -autoweight -prefix ${fmri_08_name}.run${run_label} 

	echo "[Info]: Finish register from ${fmri_06_name}.run${run_label}+orig. -> ${fmri_08_name}.run${run_label}+tlrc."

	echo "[Info]: Start Volume blur ..."

	set fmri_09_name = pb09.${fmri_00_name:r}.blur
	3dmerge -1blur_fwhm 4.0 -doall -prefix ${fmri_09_name}.run${run_label} \
		${fmri_08_name}.run${run_label}*

	set fmri_10_name = pb10.${fmri_00_name:r}.mean.rm
	3dTstat -prefix ${fmri_10_name}.run${run_label} \
		${fmri_09_name}.run${run_label}*
	
	echo "[Info]: Start mapping the volume to a range of [0,200]..."
	set mask_epi = epi_mask_onMNI152
	3dAutomask -prefix ${mask_epi}.run${run_label} ${fmri_08_name}.run${run_label}*
	
	set fmri_11_name = pb11.${fmri_00_name:r}.scale

	3dcalc -a ${fmri_09_name}.run${run_label}+tlrc \
	       -b ${fmri_10_name}.run${run_label}+tlrc \
	       -c ${mask_epi}.run${run_label}+tlrc \
	       -expr 'c * min(200, a/b*100)*step(a)*step(b)' \
	       -prefix ${fmri_11_name}.run${run_label}
	

	@ r++

end



