import netCDF4
import os
import shutil

def concatenate_adcp(adcp: str) -> None:
    source = f"/mnt/adcp/PE22_31_Shearman_ADCP_*/proc/{adcp}/contour/{adcp}.nc"
    target = f"/mnt/sci/data/Processed_NC/ADCP_UHDAS/{adcp}_concat.nc"

    # use the first of the source files as a template
    template = source.replace("*","1",1)
    if not os.path.isfile(template):
        raise FileNotFoundError(f"Source file '{template}' does not exist")

    # create the target file if it does not exist
    if not os.path.isfile(target):
        print(f"Creating file {target}")
        shutil.copy(template, target)

    # now open the target file and the source files as a multifile dataset
    with netCDF4.MFDataset(source,master_file=template) as src, \
        netCDF4.Dataset(target,'a') as tgt:

        # these datasets have no groups so we can simply loop over the variables
        for key in tgt.variables.key():
            tgt_shape = tgt[key].shape
            src_shape = src[key].shape

            # check there is new data to add
            if tgt_shape[0] >= src_shape[0]: return

            # append new data
            if len(tgt_shape) == 1:
                tgt[key][tgt_shape[0]:src_shape[0]] = src[key][tgt_shape[0]:src_shape[0]]
            elif len(tgt_shape) == 2:
                tgt[key][tgt_shape[0]:src_shape[0],:] = src[key][tgt_shape[0]:src_shape[0],:]
            else:
                raise ValueError("ADCP variables have either 1 or 2 dimensions")
        print(f"Added {src_shape[0] - tgt_shape[0]} new datapoints")












if __name__ == "__main__":
    adcp = "wh1200"
    concatenate_adcp(adcp)
