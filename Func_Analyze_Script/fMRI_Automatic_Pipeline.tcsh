#!/bin/tcsh

# The pipeline involved the necessary standard and adaptive pre-process for human brain Bold-FMRI
#
# ============== FSL =================
# 1. B0 Fieldmap Unwrapped and ApplyTopup
#
# ============== AFNI ================
# 2. Time Aligning (Concat and Shfit-aligning)
# 3. Headmotion regression
# 4. Skullstrip
# 5. Register into MNI152 for both anotomy and funcational
# 6. Post-process (Minium state, Normalization, Baseline Smoothing)
# 7. Sequence Scale
#
# ----------->
# !!! The output from the script could be calculated GLM directly !!!
#
# The script is created in 2026/06/23 by Edward Huang
#


# Check Enviroment
#
# ==================== FSL ===================
set fsl_check = 'which fsl'

if ( "$fsl_check" == "" ) then
	echo "[Error]: System cannot find FSLDIR in PATH or it never been installed in the computer..."
	echo "[Warning]: If you ensure the FSL had been installed, please follow enterin the PATH config..."
	echo "===> source ~/../data/env.sh"
	exit 1
else
	echo "[Info]: FSL is good to run! PATH: $FSLDIR"
	echo "[Info]: === FSL Version ==="   
	cat $FSLDIR/etc/fslversion
endif

if ( $#argv < 4 ) then
	echo "[Warning]: Usage: tcsh fMRI_automatic_pipeline.tcsh <epi_b0_AP.nii.gz> <epi_b0_PA.nii.gz> <epi.nii.gz> <epi.json>"
	exit 1
endif 



mkdir Analyze_Result
cd ./Analyze_Result

echo ":: :: :: :: :: ================> Start Preprocess"

# TOPUP
#
#
# B0_PA_AP pair

echo "[Info]: No.1 Topup..."

set b0_AP = $1
set b0_PA = $2
set task_epi = $3
set epi_fmri_json = $4
set epi_pair = "epi_b0_AP_PA.nii.gz"

fslmerge -t $epi_pair $b0_AP $b0_PA

# acqparams

echo "[Info]: ===> Creating acqparams.txt..."

set total_readout = `awk -F: '/"TotalReadoutTime"/ {gsub(/[ ,]/,"",$2); print $2; exit}' "$epi_fmri_json"`


# Check PhaseEncoding Direction
set pe_dir = `grep -o '"PhaseEncodingDirection": "[^"]*"' $epi_fmri_json | head -1 | sed 's/.*: "\(.*\)"/\1/'`	
if ( "$pe_dir" != "j" && "$pe_dir" != "j-" ) then
	echo "[Error]: 'PhaseEncodingDirection' must be 'j' or 'j-' for TOPUP to work correctly..."
	echo "[Info]: This script assume AP = negative while PA = positive"
endif

echo "[Info]: ===> PhaseEncodingDirection: $pe_dir (acceptable)"
echo "[Info]: ===> TotalReadoutTime: $total_readout"

# Here assume TOPUP input order:
# volume 1 = AP -> j-
# volume 2 = PA -> j

cat > acqparams.txt << EOF
0 -1 0 $total_readout
0 1 0 $total_readout
EOF

echo "[Info]: ====> Runing FSL Topup..."
topup \
	--imain=$epi_pair --datain=acqparams.txt --config=b02b0.cnf \
	       --out=topup_results --fout=fieldmap_Hz --iout=b0_corrected

echo "[Info]: Finish TOPUP"
echo "[Info]: Applying Topup to fMRI..."

if ( "$pe_dir" == "j-" ) then
	set task_inindex = 1
else if ( "$pe_dir" == "j" ) then
	set task_inindex = 2
endif

set epi_b0corrected_file = "task_epi_topup_corrected"

applytopup \
	--imain=$task_epi --datain=acqparams.txt --inindex=$task_inindex --topup=topup_results\
		--out=$epi_b0corrected_file --method=jac

echo "[Info]: Topup correction completed. Output: ${epi_b0corrected_file}.nii.gz"



# ========================= Following is AFNI Pipeline ==========================


