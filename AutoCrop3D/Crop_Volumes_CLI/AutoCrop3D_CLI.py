#!/usr/bin/env python-real

import argparse
import SimpleITK as sitk
from Crop_Volumes_utils.FilesType import Search, ChangeKeyDict
from Crop_Volumes_utils.GenerateVTKfromSeg import convertNiftiToVTK
import numpy as np
import os,json


def main(args)-> None:
    """
    Crop a Region of Interest on files with the extension .nii.gz .nrrd.gz .gipl.gz
    Input:  scan_files_path,
            path_ROI_file,
            output_path,
            suffix,
            box_Size, #checkbox in UI
            logPath # For the progress bar in UI


    """
    path_input = args.scan_files_path
    ROI_Path = args.path_ROI_file
    OutputPath = args.output_path
    suffix_namefile = args.suffix
    originalSize = args.box_Size

    with open(args.logPath,'w') as log_f:
        # clear log file
        log_f.truncate(0)
    index =0
    ScanList = Search(path_input, ".nii.gz",".nii",".nrrd.gz",".nrrd",".gipl.gz",".gipl")

    # Include case with a folder of ROI corresponding to a folder of scans
    ROIList = Search(ROI_Path,".mrk.json")

    if len(ROIList['.mrk.json']) >1:
        ROI_dict = ChangeKeyDict(ROIList)

    for key,data in ScanList.items():

        for patient_path in data:
            patient = os.path.basename(patient_path).split('_Scan')[0].split('_scan')[0].split('_Seg')[0].split('_seg')[0].split('_Or')[0].split('_OR')[0].split('_MAND')[0].split('_MD')[0].split('_MAX')[0].split('_MX')[0].split('_CB')[0].split('_lm')[0].split('_T2')[0].split('_T1')[0].split('_Cl')[0].split('.')[0]

            img = sitk.ReadImage(patient_path)

            if len(ROIList['.mrk.json']) >1:
                try:
                    ROI_Path = ROI_dict[patient]
                except:
                    print('No ROI for patient:',patient)
                    continue

            ROI = json.load(open(ROI_Path))['markups'][0]
            ROI_Center = np.array(ROI['center'])
            ROI_Size = np.array(ROI['size'])

            Lower = ROI_Center - ROI_Size / 2
            Upper = ROI_Center + ROI_Size / 2

            Lower = np.array(img.TransformPhysicalPointToContinuousIndex(Lower)).astype(int)
            Upper = np.array(img.TransformPhysicalPointToContinuousIndex(Upper)).astype(int)

            for i in range(3):
                if Lower[i] > Upper[i]:
                    Lower[i], Upper[i] = Upper[i], Lower[i]
            # Bounds checking
            img_size = img.GetSize()
            Lower = [max(0, l) for l in Lower]

            Upper = [min(img_size[i], u) for i, u in enumerate(Upper)]

            # # Ensure non-zero size for all dimensions and that lower < upper
            # for i in range(3):
            #     if Lower[i] == Upper[i]:
            #         if Upper[i] < img_size[i] - 1:
            #             Upper[i] += 1
            #         elif Lower[i] > 0:
            #             Lower[i] -= 1

            # Crop the image

            # copy img to apply changes
            img_blank = sitk.Image(img.GetSize(), img.GetPixelID())
            img_blank.CopyInformation(img)

            img_blank_arr = sitk.GetArrayFromImage(img_blank)

            # Coord of the ROI in the blank image
            size_ROI = [int(Upper[0]-Lower[0]),int(Upper[1]-Lower[1]),int(Upper[2]-Lower[2])]
            start_coord = [int(Lower[0]),int(Lower[1]),int(Lower[2])]
            end_coord = [start_coord[0]+size_ROI[0],start_coord[1]+size_ROI[1],start_coord[2]+size_ROI[2]]

            # Get only the ROI
            img_roi = img[Lower[0]:Upper[0],
                            Lower[1]:Upper[1],
                            Lower[2]:Upper[2]]

            if originalSize=='True':
                img_roi_arr = sitk.GetArrayFromImage(img_roi)

                # GetArrayFromImage return a numpy array with the shape (z,y,x)
                # Put Pixel Value in the blank image
                img_blank_arr[start_coord[2]:end_coord[2],
                                start_coord[1]:end_coord[1],
                                start_coord[0]:end_coord[0]] = img_roi_arr

                img_crop = sitk.GetImageFromArray(img_blank_arr)
                img_crop.CopyInformation(img_blank)

            else:
                img_crop = img_roi

            # Create the output path
            # relative_path = all folder to get to the file we want in the input
            relative_path = os.path.relpath(patient_path,path_input)
            filename_interm = os.path.basename(patient_path).split('.')[0]
            filename = filename_interm + "_"+ suffix_namefile + key

            vtk_filename = filename_interm + "_" + suffix_namefile + "_vtk.vtk"
            ScanOutPath = os.path.join(OutputPath,relative_path).replace(os.path.basename(relative_path),filename)

            VTKOutPath = os.path.join(OutputPath,relative_path).replace(os.path.basename(relative_path),vtk_filename)

            os.makedirs(os.path.dirname(ScanOutPath), exist_ok=True)

            try:

                sitk.WriteImage(img_crop,ScanOutPath)

            except:
                import sys
                print("Error for patient: ",patient)
                print('The error says: ',sys.exc_info()[0])
                print('Lower: ',Lower)
                print('Upper: ',Upper)
                print('Lower[2]:',Lower[2])
                print('Upper[2]:',Upper[2])

            with open(args.logPath,'r+') as log_f :
                    log_f.write(str(index))

            if "seg" in ScanOutPath.lower():
                try :
                    convertNiftiToVTK(ScanOutPath,VTKOutPath)
                except :
                    pass

            index+=1


if __name__ == "__main__":

    parser = argparse.ArgumentParser()


    parser.add_argument('scan_files_path',type=str)
    parser.add_argument('path_ROI_file',type=str)
    parser.add_argument("output_path",type=str)
    parser.add_argument('suffix',type=str)
    parser.add_argument('box_Size',type=str)
    parser.add_argument('logPath',type=str)


    args = parser.parse_args()


    main(args)