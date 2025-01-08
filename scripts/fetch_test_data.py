"""
Fetch test data

Fetch and downscale test data from ESGF.
"""

import os
import pathlib
from pathlib import Path
from typing import Any

import xarray as xr
from intake_esgf import ESGFCatalog

OUTPUT_PATH = Path("data")


def fetch_datasets(search_facets: dict[str, Any], remove_ensembles: bool) -> list[Path]:
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

    path_dict = cat.to_path_dict(prefer_streaming=False)

    # Flatten list of lists into a single list
    return [p for dataset_paths in path_dict.values() for p in dataset_paths]


def downscale_dataset(dataset: xr.Dataset) -> xr.Dataset:
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


def create_out_filename(ds: xr.Dataset) -> pathlib.Path:
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
        "activity_id",
        "institution_id",
        "source_id",
        "experiment_id",
        "variant_label",
        "table_id",
        "variable_id",
        "grid_label",
        "version",
    ]

    cmip6_filename_paths = [
        "variable_id",
        "table_id",
        "source_id",
        "experiment_id",
        "variant_label",
        "grid_label",
    ]

    output_path = Path(os.path.join(*[str(ds.attrs[item]) for item in cmip6_path_items]))

    if "time" in ds.dims:
        time_range = f"{ds.time.min().dt.strftime('%Y%m').item()}-{ds.time.max().dt.strftime('%Y%m').item()}"
        filename = "_".join([str(ds.attrs[item]) for item in cmip6_filename_paths]) + f"_{time_range}.nc"
    else:
        filename = "_".join([str(ds.attrs[item]) for item in cmip6_filename_paths]) + ".nc"
    return output_path / filename


if __name__ == "__main__":
    datasets: list[Path] = []

    facets_to_fetch = [
        dict(
            source_id="ACCESS-ESM1-5",
            frequency="mon",
            variable_id=["tas", "rsut", "rlut", "rsdt"],
            experiment_id=["ssp119", "ssp126", "historical"],
            remove_ensembles=True,
        ),
    ]

    for facets in facets_to_fetch:
        remove_ensembles = facets.pop("remove_ensembles", False)
        datasets.extend(fetch_datasets(facets, remove_ensembles=remove_ensembles))

    print(datasets)
    for dataset_path in datasets:
        ds_orig = xr.open_dataset(dataset_path)

        ds_downscaled = downscale_dataset(ds_orig)

        output_filename = OUTPUT_PATH / create_out_filename(ds_orig)
        output_filename.parent.mkdir(parents=True, exist_ok=True)
        ds_downscaled.to_netcdf(output_filename)
