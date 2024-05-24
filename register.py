import os
import subprocess
import nibabel as nib
from nilearn.image import resample_img
import numpy as np
import argparse

# Function to calculate image center coordinates
def get_image_center(image):
    aff = image.affine
    shape = image.shape
    center_coords = np.array(shape) // 2
    center_coords = np.hstack((center_coords, 1))
    return aff.dot(center_coords)[:3]

# Function to perform coregistration using FSL's FLIRT
def flirt_coregister(reference_path, moving_path, output_path, dof, interpolation):
    flirt_output = os.path.splitext(output_path)[0]  # Remove extension from output_path
    flirt_cmd = f"flirt -in {moving_path} -ref {reference_path} -out {output_path} -omat {flirt_output}.mat -dof {dof} -cost mutualinfo -interp {interpolation}"
    subprocess.run(flirt_cmd, shell=True)

# Function to perform coregistration using Python's resample_img
def python_coregister(reference_path, moving_path, output_path, translation, interpolation='continuous'):
    reference_img = nib.load(reference_path)
    moving_img = nib.load(moving_path)

    # Apply translation to the affine matrix
    translation_matrix = np.eye(4)
    translation_matrix[:3, 3] = translation

    # Combine the translation with the reference image affine
    new_affine = np.dot(translation_matrix, reference_img.affine)

    # Resample moving image with the new affine
    moving_resampled = resample_img(moving_img, target_affine=new_affine,
                                    target_shape=reference_img.shape,
                                    interpolation=interpolation,
                                    clip=True,
                                    fill_value=0.0)

    # Print center coordinates before and after resampling
    reference_center_before = get_image_center(reference_img)
    reference_center_after = get_image_center(moving_resampled)
    print("Center coordinates before resampling:", reference_center_before)
    print("Center coordinates after resampling:", reference_center_after)

    # Save coregistered image
    nib.save(moving_resampled, output_path)

def main(root_path):
    # Paths
    nifti_path = os.path.join(root_path, "nifti/")
    template_path = os.path.join(root_path, "temp/")
    output_path = os.path.join(root_path, "output/")

    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)

    # Find reference image ending with "MPRAGE.nii.gz" in nifti directory
    reference_files = [file for file in os.listdir(nifti_path) if file.endswith("MPRAGE.nii.gz")]
    if len(reference_files) == 1:
        reference_path = os.path.join(nifti_path, reference_files[0])
    else:
        print("Error: Unable to find reference image.")
        return

    # Find moving image ending with "MPRAGE_FSGAD.nii.gz" in nifti directory
    moving_files = [file for file in os.listdir(nifti_path) if file.endswith("MPRAGE_FSGAD.nii.gz")]
    if len(moving_files) == 1:
        moving_path = os.path.join(nifti_path, moving_files[0])
    else:
        print("Error: Unable to find moving image.")
        return

    if reference_path and moving_path:
        flirt_post_to_pre_path = os.path.join(output_path, "flirt_post_to_pre.nii.gz")
        flirt_coregister(reference_path, moving_path, flirt_post_to_pre_path, dof=6, interpolation='trilinear')
    else:
        print("Error: Coregistration failed due to missing reference or moving image.")
        return

    # Find images with specified names in template directory
    template_files = os.listdir(template_path)
    template_t1_name = "template.nii.gz"
    template_mask_name = "mask_brain.nii.gz"
    template_atlas_name = "atlas.nii.gz"

    template_t1_path = None
    template_mask_path = None
    template_atlas_path = None

    for file in template_files:
        if file.endswith(template_t1_name):
            template_t1_path = os.path.join(template_path, file)
        elif file.endswith(template_mask_name):
            template_mask_path = os.path.join(template_path, file)
        elif file.endswith(template_atlas_name):
            template_atlas_path = os.path.join(template_path, file)

    if all([template_t1_path, template_mask_path, template_atlas_path]):
        flirt_template_t1_in_pre_space_path = os.path.join(output_path, "flirt_Template_T1_in_pre_space.nii.gz")
        flirt_template_mask_in_pre_space_path = os.path.join(output_path, "flirt_Template_mask_in_pre_space.nii.gz")
        flirt_template_atlas_in_pre_space_path = os.path.join(output_path, "flirt_Template_atlas_in_pre_space.nii.gz")

        # Perform FSL's FLIRT co-registration between the reference_path and the template_t1_path
        flirt_coregister(reference_path, template_t1_path, flirt_template_t1_in_pre_space_path, dof=12, interpolation='trilinear' )

        # Calculate translation to be used in coregistration
        reference_center = get_image_center(nib.load(reference_path))
        moving_center = get_image_center(nib.load(flirt_template_t1_in_pre_space_path))
        translation = reference_center - moving_center

        # Apply FLIRT transformation to template_mask_path and template_atlas_path
        flirt_mat_file = os.path.join(output_path, "flirt_Template_T1_in_pre_space.mat")
        flirt_cmd = f"flirt -in {template_mask_path} -ref {reference_path} -out {flirt_template_mask_in_pre_space_path} -applyxfm -init {flirt_mat_file}"
        subprocess.run(flirt_cmd, shell=True)

        flirt_cmd = f"flirt -in {template_atlas_path} -ref {reference_path} -out {flirt_template_atlas_in_pre_space_path} -applyxfm -init {flirt_mat_file} -interp nearestneighbour"
        subprocess.run(flirt_cmd, shell=True)

        # Coregister template images to pre_contrast image using Python's resample_img
        python_template_t1_in_pre_space_path = os.path.join(output_path, "python_Template_T1_in_pre_space.nii.gz")
        python_template_mask_in_pre_space_path = os.path.join(output_path, "python_Template_mask_in_pre_space.nii.gz")
        #python_template_atlas_in_pre_space_path = os.path.join(output_path, "python_Template_atlas_in_pre_space.nii.gz")

        python_coregister(reference_path, flirt_template_t1_in_pre_space_path, python_template_t1_in_pre_space_path, translation)
        python_coregister(reference_path, flirt_template_mask_in_pre_space_path, python_template_mask_in_pre_space_path, translation)
        #python_coregister(reference_path, flirt_template_atlas_in_pre_space_path, python_template_atlas_in_pre_space_path, translation)
    else:
        print("Error: Unable to find template images.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Coregister medical images using FSL and Python.')
    parser.add_argument('root_path', type=str, help='Root path containing nifti, temp, and output directories.')
    args = parser.parse_args()
    main(args.root_path)
