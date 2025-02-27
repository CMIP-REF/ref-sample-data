from pathlib import Path

import pandas as pd
import pooch
import xarray as xr
from intake_esgf import ESGFCatalog

from sample_data import CMIP6Request, DataRequest, Obs4MIPsRequest

OUTPUT_PATH = Path("data")


def fetch_datasets(request: DataRequest) -> pd.DataFrame:
    """
    Fetch the datasets from ESGF.

    Parameters
    ----------
    request
        The request object

    Returns
    -------
        Dataframe that contains metadata and paths to the fetched datasets
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
    pooch.make_registry(str(OUTPUT_PATH), "registry.txt")


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
        # PMP PDO data
        CMIP6Request(
            facets=dict(
                source_id="ACCESS-ESM1-5",
                frequency=["fx", "mon"],
                variable_id=["areacella", "ts"],
                experiment_id=["historical", "hist-GHG"],
                variant_label=["r1i1p1f1", "r2i1p1f1"],
            ),
            remove_ensembles=False,
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

    for dataset_requested in datasets_to_fetch:
        create_sample_dataset(dataset_requested)
