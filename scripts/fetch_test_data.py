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


def fetch_datasets(
    search_facets: dict[str, Any], remove_ensembles: bool, time_span: tuple[str, str] | None
) -> pd.DataFrame:
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
    if time_span:
        merged_df["time_start"] = time_span[0]
        merged_df["time_end"] = time_span[1]

    return merged_df


def deduplicate_datasets(datasets: pd.DataFrame) -> pd.DataFrame:
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

    def _deduplicate_group(group: pd.DataFrame) -> pd.DataFrame:
        first = group.iloc[0].copy()
        first.time_start = group.time_start.min()
        first.time_end = group.time_end.max()

        return first

    return datasets.groupby("key").apply(_deduplicate_group, include_groups=False).reset_index()


def decimate_dataset(dataset: xr.Dataset, time_span: tuple[str, str] | None) -> xr.Dataset | None:
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
    result = dataset.interp(lat=dataset.lat[::10], lon=dataset.lon[::10])

    if "time" in dataset.dims and time_span is not None:
        result = result.sel(time=slice(*time_span))
        if result.time.size == 0:
            result = None

    return result


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
        dict(
            source_id="ACCESS-ESM1-5",
            frequency=["fx", "mon"],
            variable_id=["areacella", "tas", "rsut", "rlut", "rsdt"],
            experiment_id=["ssp126", "historical"],
            remove_ensembles=True,
            time_span=("2000", "2025"),
        ),
    ]

    dataset_metadata_collection: list[pd.DataFrame] = []
    for facets in facets_to_fetch:
        dataset_metadata_collection.append(
            fetch_datasets(
                facets,
                remove_ensembles=facets.pop("remove_ensembles", False),
                time_span=facets.pop("time_span", None),
            )
        )

    # Combine all datasets
    datasets = deduplicate_datasets(pd.concat(dataset_metadata_collection))

    for _, dataset in datasets.iterrows():
        print(dataset.key)
        for ds_filename in dataset["files"]:
            ds_orig = xr.open_dataset(ds_filename)

            ds_decimated = decimate_dataset(ds_orig, time_span=(dataset["time_start"], dataset["time_end"]))
            if ds_decimated is None:
                continue

            output_filename = OUTPUT_PATH / create_out_filename(dataset, ds_decimated)
            output_filename.parent.mkdir(parents=True, exist_ok=True)
            ds_decimated.to_netcdf(output_filename)

    # Regenerate the registry.txt file
    pooch.make_registry(OUTPUT_PATH, "registry.txt")
