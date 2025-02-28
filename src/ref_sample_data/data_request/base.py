import pathlib
from typing import Protocol

import pandas as pd
import xarray as xr


class DataRequest(Protocol):
    """
    Represents a request for a dataset

    A polymorphic association is used to capture the different types of datasets as each
    dataset type may have different metadata fields and may need to be handled
    differently to generate the sample data.
    """

    facets: dict[str, str | tuple[str, ...]]
    remove_ensembles: bool
    time_span: tuple[str, str]

    def decimate_dataset(self, dataset: xr.Dataset, time_span: tuple[str, str] | None) -> xr.Dataset | None:
        """Downscale the dataset to a smaller size."""
        ...

    def generate_filename(
        self, metadata: pd.Series, ds: xr.Dataset, ds_filename: pathlib.Path
    ) -> pathlib.Path:
        """Create the output filename for the dataset."""
        ...
