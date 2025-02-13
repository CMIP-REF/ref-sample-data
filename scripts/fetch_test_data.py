import os
import pathlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd
import pooch
import xarray as xr
from intake_esgf import ESGFCatalog

OUTPUT_PATH = Path("data")


class DataRequest(ABC):
    """
    Represents a request for a dataset

    A polymorphic association is used to capture the different types of datasets as each
    dataset type may have different metadata fields and may need to be handled
    differently to generate the sample data.
    """

    def __init__(self, remove_ensembles: bool, time_span: tuple[str, str]):
        self.remove_ensembles = remove_ensembles
        self.time_span = time_span

    @abstractmethod
    def decimate_dataset(self, dataset: xr.Dataset, time_span: tuple[str, str] | None) -> xr.Dataset | None:
        """Downscale the dataset to a smaller size."""
        pass

    @abstractmethod
    def create_out_filename(self, metadata: pd.Series, ds: xr.Dataset, ds_filename: str) -> pathlib.Path:
        """Create the output filename for the dataset."""
        pass


class CMIP6Request(DataRequest):
    """
    Represents a CMIP6 dataset request

    """

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

        super().__init__(remove_ensembles, time_span)

        self.cmip6_path_items = [
            "mip_era",
            "activity_drs",
            "institution_id",
            "source_id",
            "experiment_id",
            "member_id",
            "table_id",
            "variable_id",
            "grid_label",
        ]

        self.cmip6_filename_paths = [
            "variable_id",
            "table_id",
            "source_id",
            "experiment_id",
            "member_id",
            "grid_label",
        ]

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

    def create_out_filename(self, metadata: pd.Series, ds: xr.Dataset, ds_filename: str) -> pathlib.Path:
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


class Obs4MIPsRequest(DataRequest):
    """
    Represents a Obs4MIPs dataset request

    """

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

    def create_out_filename(self, metadata: pd.Series, ds: xr.Dataset, ds_filename: str) -> pathlib.Path:
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


def fetch_datasets(request: DataRequest) -> pd.DataFrame:
    """
    Fetch the datasets from ESGF.

    Parameters
    ----------
    search_facets
        Facets to search for
    remove_ensembles
        Whether to remove ensembles from the dataset
        (i.e. include only a single ensemble member)

    Returns
    -------
    List of paths to the fetched datasets
    """
    cat = ESGFCatalog()

    cat.search(**request.facets)
    if request.remove_ensembles:
        cat.remove_ensembles()

    path_dict = cat.to_path_dict(prefer_streaming=False, minimal_keys=False)
    merged_df = cat.df.merge(pd.Series(path_dict, name="files"), left_on="key", right_index=True)
    if request.time_span:
        merged_df["time_start"] = request.time_span[0]
        merged_df["time_end"] = request.time_span[1]
    return merged_df


def deduplicate_datasets(request: DataRequest) -> pd.DataFrame:
    """
    Deduplicate a dataset collection.

    Uses the metadata from the first dataset in each group,
    but expands the time range to the min/max timespan of the group.

    Parameters
    ----------
    datasets
        The dataset collection

    Returns
    -------
    pd.DataFrame
        The deduplicated dataset collection spanning the times requested
    """
    datasets = fetch_datasets(request)

    def _deduplicate_group(group: pd.DataFrame) -> pd.DataFrame:
        first = group.iloc[0].copy()
        first.time_start = group.time_start.min()
        first.time_end = group.time_end.max()

        return first

    return datasets.groupby("key").apply(_deduplicate_group, include_groups=False).reset_index()


def create_sample_dataset(request: DataRequest):
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
    datasets = deduplicate_datasets(request)
    for _, dataset in datasets.iterrows():
        for ds_filename in dataset["files"]:
            ds_orig = xr.open_dataset(ds_filename)
            ds_decimated = request.decimate_dataset(ds_orig, request.time_span)
            if ds_decimated is None:
                continue

            output_filename = OUTPUT_PATH / request.create_out_filename(dataset, ds_decimated, ds_filename)
            output_filename.parent.mkdir(parents=True, exist_ok=True)
            ds_decimated.to_netcdf(output_filename)

    # Regenerate the registry.txt file
    pooch.make_registry(OUTPUT_PATH, "registry.txt")


if __name__ == "__main__":
    datasets_to_fetch = [
        # Example metric data
        CMIP6Request(
            facets=dict(
                source_id="ACCESS-ESM1-5",
                frequency=["fx", "mon"],
                variable_id=["areacella", "tas", "tos", "rsut", "rlut", "rsdt"],
                experiment_id=["ssp126", "historical"],
            ),
            remove_ensembles=True,
            time_span=("2000", "2025"),
        ),
        # ESMValTool ECS data
        CMIP6Request(
            facets=dict(
                source_id="ACCESS-ESM1-5",
                frequency=["fx", "mon"],
                variable_id=["areacella", "rlut", "rsdt", "rsut", "tas"],
                experiment_id=["abrupt-4xCO2", "piControl"],
            ),
            remove_ensembles=True,
            time_span=("0101", "0125"),
        ),
        # ESMValTool TCR data
        CMIP6Request(
            facets=dict(
                source_id="ACCESS-ESM1-5",
                frequency=["fx", "mon"],
                variable_id=["areacella", "tas"],
                experiment_id=["1pctCO2", "piControl"],
            ),
            remove_ensembles=True,
            time_span=("0101", "0180"),
        ),
        # ILAMB data
        CMIP6Request(
            facets=dict(
                source_id="ACCESS-ESM1-5",
                frequency=["fx", "mon"],
                variable_id=["areacella", "sftlf", "gpp", "pr"],
                experiment_id=["historical"],
            ),
            remove_ensembles=True,
            time_span=("2000", "2025"),
        ),
        # Obs4MIPs AIRS data
        Obs4MIPsRequest(
            facets=dict(
                project="obs4MIPs",
                institution_id="NASA-JPL",
                frequency="mon",
                source_id="AIRS-2-1",
                variable_id="ta",
            ),
            remove_ensembles=False,
            time_span=("2002", "2016"),
        ),
    ]

    for dataset_requested in datasets_to_fetch[3:4]:
        create_sample_dataset(dataset_requested)
