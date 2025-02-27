import os.path
from pathlib import Path
from typing import Any

import pandas as pd
import xarray as xr

from ref_sample_data.data_request.base import DataRequest


class Obs4MIPsRequest(DataRequest):
    """
    Represents a Obs4MIPs dataset request
    """

    obs4mips_path_items = (
        "activity_id",
        "institution_id",
        "source_id",
        "variable_id",
        "grid_label",
    )

    obs4mips_filename_paths = (
        "variable_id",
        "source_id",
        "grid_label",
    )

    def __init__(self, facets: dict[str, Any], remove_ensembles: bool, time_span: tuple[str, str] | None):
        self.avail_facets = [
            "activity_id",
            "institution_id",
            "source_id",
            "frequency",
            "variable_id",
            "grid_label",
            "version",
            "data_node",
        ]

        self.facets = facets
        self.remove_ensembles = remove_ensembles
        self.time_span = time_span

        super().__init__(remove_ensembles, time_span)

        self.obs4mips_path_items = [
            "activity_id",
            "institution_id",
            "source_id",
            "variable_id",
            "grid_label",
        ]

        self.obs4mips_filename_paths = [
            "variable_id",
            "source_id",
            "grid_label",
        ]

        assert all(key in self.avail_facets for key in self.obs4mips_path_items), "Error message"
        assert all(key in self.avail_facets for key in self.obs4mips_filename_paths), "Error message"

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

    def generate_filename(self, metadata: pd.Series, ds: xr.Dataset, ds_filename: str) -> Path:
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
            Path(os.path.join(*[metadata[item] for item in self.obs4mips_path_items]))
            / f"v{metadata['version']}"
        )
        if ds_filename.name.split("_")[0] == ds.variable_id:
            filename_prefix = "_".join([metadata[item] for item in self.obs4mips_filename_paths])
        else:
            filename_prefix = ds_filename.name.split("_")[0] + "_"
            filename_prefix += "_".join(
                [metadata[item] for item in self.obs4mips_filename_paths if item != "variable_id"]
            )

        if "time" in ds.dims:
            time_range = (
                f"{ds.time.min().dt.strftime('%Y%m').item()}-{ds.time.max().dt.strftime('%Y%m').item()}"
            )
            filename = f"{filename_prefix}_{time_range}.nc"
        else:
            filename = f"{filename_prefix}.nc"

        return output_path / filename
