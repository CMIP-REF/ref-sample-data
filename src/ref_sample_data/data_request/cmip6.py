import os.path
import pathlib
from pathlib import Path
from typing import Any

import pandas as pd
import xarray as xr

from ref_sample_data.data_request.base import DataRequest
from ref_sample_data.resample import decimate_curvilinear, decimate_rectilinear


def prefix_to_filename(ds, filename_prefix: str) -> str:
    """
    Create a filename from a dataset and a prefix.

    Optionally includes the time range of the dataset if it has a time dimension.

    Parameters
    ----------
    ds
        Dataset
    filename_prefix
        Prefix for the filename

        This includes the different facets of the dataset

    Returns
    -------
        Filename for the dataset
    """
    if "time" in ds.dims:
        time_range = f"{ds.time.min().dt.strftime('%Y%m').item()}-{ds.time.max().dt.strftime('%Y%m').item()}"
        filename = f"{filename_prefix}_{time_range}.nc"
    else:
        filename = f"{filename_prefix}.nc"
    return filename


class CMIP6Request(DataRequest):
    """
    Represents a CMIP6 dataset request

    """

    cmip6_path_items = (
        "mip_era",
        "activity_drs",
        "institution_id",
        "source_id",
        "experiment_id",
        "member_id",
        "table_id",
        "variable_id",
        "grid_label",
    )

    cmip6_filename_paths = (
        "variable_id",
        "table_id",
        "source_id",
        "experiment_id",
        "member_id",
        "grid_label",
    )

    def __init__(self, facets: dict[str, Any], remove_ensembles: bool, time_span: tuple[str, str] | None):
        self.avail_facets = [
            "mip_era",
            "activity_drs",
            "institution_id",
            "source_id",
            "experiment_id",
            "member_id",
            "table_id",
            "variable_id",
            "grid_label",
            "version",
            "data_node",
        ]

        self.facets = facets
        self.remove_ensembles = remove_ensembles
        self.time_span = time_span

        assert all(key in self.avail_facets for key in self.cmip6_path_items), "Error message"
        assert all(key in self.avail_facets for key in self.cmip6_filename_paths), "Error message"

    def decimate_dataset(self, dataset: xr.Dataset, time_span: tuple[str, str] | None) -> xr.Dataset | None:
        """
        Downscale the dataset to a smaller size.

        Parameters
        ----------
        dataset
            The dataset to downscale
        time_span
            The time span to extract from a dataset

        Returns
        -------
        xr.Dataset
            The downscaled dataset
        """
        has_latlon = "lat" in dataset.dims and "lon" in dataset.dims
        has_ij = "i" in dataset.dims and "j" in dataset.dims

        if has_latlon:
            assert len(dataset.lat.dims) == 1 and len(dataset.lon.dims) == 1

            result = decimate_rectilinear(dataset)
        elif has_ij:
            # 2d curvilinear grid (generally ocean variables)
            result = decimate_curvilinear(dataset)
        else:
            raise ValueError("Cannot decimate this grid: too many dimensions")

        if "time" in dataset.dims and time_span is not None:
            result = result.sel(time=slice(*time_span))
            if result.time.size == 0:
                result = None

        return result

    def generate_filename(self, metadata: pd.Series, ds: xr.Dataset, ds_filename: pathlib.Path) -> Path:
        """
        Create the output filename for the dataset.

        Parameters
        ----------
        ds
            Loaded dataset

        ds_filename:
            Filename of the dataset (Unused)

        Returns
        -------
            The output filename
        """
        output_path = (
            Path(os.path.join(*[metadata[item] for item in self.cmip6_path_items]))
            / f"v{metadata['version']}"
        )
        filename_prefix = "_".join([metadata[item] for item in self.cmip6_filename_paths])

        return output_path / prefix_to_filename(ds, filename_prefix)
