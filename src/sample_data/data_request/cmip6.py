import os.path
from pathlib import Path
from typing import Any

import pandas as pd
import xarray as xr

from sample_data.data_request.base import DataRequest


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
            result = dataset.interp(lat=dataset.lat[:10], lon=dataset.lon[:10])
        elif has_ij:
            # 2d lat/lon grid (generally ocean variables)
            # Choose a starting point around the middle of the grid to maximise chance that it has values
            # TODO: Be smarter about this?
            j_midpoint = len(dataset.j) // 2
            result = dataset.interp(i=dataset.i[:10], j=dataset.j[j_midpoint : j_midpoint + 10])
        else:
            raise ValueError("Cannot decimate this grid: too many dimensions")

        if "time" in dataset.dims and time_span is not None:
            result = result.sel(time=slice(*time_span))
            if result.time.size == 0:
                result = None

        return result

    def create_out_filename(self, metadata: pd.Series, ds: xr.Dataset, ds_filename: str) -> Path:
        """
        Create the output filename for the dataset.

        Parameters
        ----------
        ds
            Loaded dataset

        Returns
        -------
            The output filename
        """
        output_path = (
            Path(os.path.join(*[metadata[item] for item in self.cmip6_path_items]))
            / f"v{metadata['version']}"
        )
        filename_prefix = "_".join([metadata[item] for item in self.cmip6_filename_paths])

        if "time" in ds.dims:
            time_range = (
                f"{ds.time.min().dt.strftime('%Y%m').item()}-{ds.time.max().dt.strftime('%Y%m').item()}"
            )
            filename = f"{filename_prefix}_{time_range}.nc"
        else:
            filename = f"{filename_prefix}.nc"

        return output_path / filename
