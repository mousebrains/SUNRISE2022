import netCDF4
import os
import xarray as xr

def concatenate_adcp(adcp: str) -> None:
    source = f"/mnt/adcp/PE22_31_Shearman_ADCP_*/proc/{adcp}/contour/{adcp}.nc"
    target = f"/mnt/sci/data/Processed_NC/ADCP_UHDAS/{adcp}_concat.nc"

    # create the target file if it does not exist
    if not os.path.isfile(target):

        # use the first of the source files as a template
        # however we need to ensure the time dimension is unlimited
        # therefore use xarray to do the copy
        template = source.replace("*","1",1)
        if not os.path.isfile(template):
            raise FileNotFoundError(f"Source file '{template}' does not exist")
        tmp = xr.open_dataset(template)
        tmp.to_netcdf(target,unlimited_dims=("time"),format="NETCDF3_CLASSIC")
        print(f"Created file {target}")

    # now open the target file and the source files as a multifile dataset
    with netCDF4.MFDataset(source,aggdim='time') as src, \
        netCDF4.Dataset(target,'a') as tgt:


        # these datasets have no groups so we can simply loop over the variables
        for key in tgt.variables.keys():
            tgt_shape = tgt[key].shape
            src_shape = src[key].shape

            # skip scalar variables
            if not tgt_shape:
                continue
            else:
                tgt_idx = tgt_shape[0]
                src_idx = src_shape[0]

            # check there is new data to add
            if tgt_idx >= src_idx: continue

            # append new data
            if len(tgt_shape) == 1:
                tgt[key][tgt_idx:src_idx] = src[key][tgt_idx:src_idx]
            elif len(tgt_shape) == 2:
                tgt[key][tgt_idx:src_idx,:] = src[key][tgt_idx:src_idx,:]
            else:
                raise ValueError("ADCP variables have either 1 or 2 dimensions")
        print(f"Added {src_shape[0] - tgt_shape[0]} new datapoints")












if __name__ == "__main__":
    adcp = "wh1200"
    concatenate_adcp(adcp)
