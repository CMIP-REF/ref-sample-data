"""
Fetch test data

Fetch and downscale test data from ESGF.
"""

import os
import pathlib
from pathlib import Path
from typing import Any

import pandas as pd
import pooch
import xarray as xr
from intake_esgf import ESGFCatalog

OUTPUT_PATH = Path("data")


def fetch_datasets(search_facets: dict[str, Any], remove_ensembles: bool) -> pd.DataFrame:
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

    cat.search(**search_facets)
    if remove_ensembles:
        cat.remove_ensembles()

    path_dict = cat.to_path_dict(prefer_streaming=False, minimal_keys=False)

    merged_df = cat.df.merge(pd.Series(path_dict, name="files"), left_on="key", right_index=True)

    return merged_df


def decimate_dataset(dataset: xr.Dataset) -> xr.Dataset:
    """
    Downscale the dataset to a smaller size.

    Parameters
    ----------
    dataset
        The dataset to downscale

    Returns
    -------
    xr.Dataset
        The downscaled dataset
    """
    spatial_downscale = dataset.interp(lat=dataset.lat[::10], lon=dataset.lon[::10])

    if "time" in dataset.dims:
        return spatial_downscale.sel(time=spatial_downscale.time[::6])

    return spatial_downscale


def create_out_filename(metadata: pd.Series, ds: xr.Dataset) -> pathlib.Path:
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
    cmip6_path_items = [
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

    cmip6_filename_paths = [
        "variable_id",
        "table_id",
        "source_id",
        "experiment_id",
        "member_id",
        "grid_label",
    ]

    output_path = (
        Path(os.path.join(*[metadata[item] for item in cmip6_path_items])) / f"v{metadata['version']}"
    )
    filename_prefix = "_".join([metadata[item] for item in cmip6_filename_paths])

    if "time" in ds.dims:
        time_range = f"{ds.time.min().dt.strftime('%Y%m').item()}-{ds.time.max().dt.strftime('%Y%m').item()}"
        filename = f"{filename_prefix}_{time_range}.nc"
    else:
        filename = f"{filename_prefix}.nc"
    return output_path / filename


if __name__ == "__main__":
    facets_to_fetch = [
        # Example metric data
        dict(
            source_id="ACCESS-ESM1-5",
            frequency="mon",
            variable_id=["tas", "rsut", "rlut", "rsdt"],
            experiment_id=["ssp126", "historical"],
            remove_ensembles=True,
        ),
        dict(
            source_id="ACCESS-ESM1-5",
            frequency="fx",
            variable_id=["areacella"],
            experiment_id=["ssp126", "historical"],
            remove_ensembles=True,
        ),
        # ESMValTool ECS data
        dict(
            source_id="ACCESS-ESM1-5",
            frequency=["fx", "mon"],
            variable_id=["areacella", "rlut", "rsdt", "rsut", "tas"],
            experiment_id=["abrupt-4xCO2", "piControl"],
            remove_ensembles=True,
        ),
        # ESMValTool TCR data
        dict(
            source_id="ACCESS-ESM1-5",
            frequency=["fx", "mon"],
            variable_id=["areacella", "tas"],
            experiment_id=["1pctCO2", "piControl"],
            remove_ensembles=True,
        ),
    ]

    dataset_metadata_collection: list[pd.DataFrame] = []
    for facets in facets_to_fetch:
        remove_ensembles = facets.pop("remove_ensembles", False)

        dataset_metadata_collection.append(fetch_datasets(facets, remove_ensembles=remove_ensembles))

    datasets = pd.concat(dataset_metadata_collection)

    for _, dataset in datasets.iterrows():
        print(dataset.key)
        for ds_filename in dataset["files"]:
            ds_orig = xr.open_dataset(ds_filename)

            ds_downscaled = decimate_dataset(ds_orig)

            output_filename = OUTPUT_PATH / create_out_filename(dataset, ds_orig)
            output_filename.parent.mkdir(parents=True, exist_ok=True)
            ds_downscaled.to_netcdf(output_filename)

    pooch.make_registry(OUTPUT_PATH, "registry.txt")
