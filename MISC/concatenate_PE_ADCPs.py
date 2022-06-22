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
        if adcp == "wh600":
            template = source.replace("*","2",1)
        else:
            template = source.replace("*","1",1)
        if not os.path.isfile(template):
            raise FileNotFoundError(f"Source file '{template}' does not exist")
        tmp = xr.open_dataset(template)
        tmp.to_netcdf(target,unlimited_dims=("time"),format="NETCDF3_CLASSIC")
        print(f"Created file {target}")

    # now open the target file and the source files as a multifile dataset
    with netCDF4.MFDataset(source,aggdim='time') as src, \
        netCDF4.Dataset(target,'a') as tgt:

        tgt_idx = tgt.time.size
        src_idx = src.time.size
        print(f"{adcp}: Target length = {tgt_idx}, Source length = {src_idx})

        # check there is new data to add
        if tgt_idx >= src_idx: return

        # these datasets have no groups so we can simply loop over the variables
        for key in tgt.variables.keys():
            tgt_shape = tgt[key].shape
            src_shape = src[key].shape

            # skip scalar variables
            if not tgt_shape: continue

            # append new data
            if len(tgt_shape) == 1:
                tgt[key][tgt_idx:src_idx] = src[key][tgt_idx:src_idx]
            elif len(tgt_shape) == 2:
                tgt[key][tgt_idx:src_idx,:] = src[key][tgt_idx:src_idx,:]
            else:
                raise ValueError("ADCP variables have either 1 or 2 dimensions")












if __name__ == "__main__":
    concatenate_adcp("wh1200")
    concatenate_adcp("wh600")
    concatenate_adcp("wh300")
