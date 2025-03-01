import numpy as np
import xarray as xr
import xcdat


def _calculate_2d_cell_bounds(
    dimension: xr.DataArray,
    i: int,
    j: int,
) -> [float, float, float, float]:
    cell_center = dimension[j, i].data
    if i == 0:
        di = dimension[j, i + 1].data - cell_center
    else:
        di = cell_center - dimension[j, i - 1].data
    if j == 0:
        dj = dimension[j + 1, i].data - cell_center
    else:
        dj = cell_center - dimension[j - 1, i].data

    return np.asarray(
        [
            cell_center - dj / 2 - di / 2,
            cell_center - dj / 2 + di / 2,
            cell_center + dj / 2 + di / 2,
            cell_center + dj / 2 - di / 2,
        ]
    ).tolist()


def decimate_rectilinear(dataset: xr.Dataset) -> xr.Dataset:
    """
    Decimate a rectilinear gridded dataset.

    Parameters
    ----------
    dataset
        Dataset to decimate

    Returns
    -------
        Resampled dataset with a 10x10 degree grid
    """
    # Decimate the dataset, but update the bounds
    # 10x10 degree grid
    for data_var in dataset.data_vars:
        # Some datasets don't correctly use data_vars
        if "_bnds" in data_var:
            continue
        output_grid = xcdat.create_uniform_grid(-90, 90, 10, 0, 360, 10)
        dataset = dataset.regridder.horizontal(
            data_var,
            output_grid=output_grid,
            tool="xesmf",
            method="bilinear",
        )
    return dataset


def decimate_curvilinear(dataset: xr.Dataset, factor: int = 10) -> xr.Dataset:
    """
    Decimate a curvilinear gridded dataset.

    Generally ocean variables use a curvilinear grid where the lat/lon coordinates are 2D arrays.

    Parameters
    ----------
    dataset
        Dataset to decimate
    factor
        Factor to decimate the dataset

        10 would result in a dataset with 1/10th the resolution

    Returns
    -------
        Resampled dataset
    """
    assert factor >= 1
    result = dataset.interp(i=dataset.i[::factor]).interp(j=dataset.j[::factor])
    result.coords["i"].values[:] = range(len(result.i))
    result.coords["j"].values[:] = range(len(result.j))

    # Update the bounds of the cells
    for j in result.j:
        for i in result.i:
            result.vertices_latitude[j, i] = _calculate_2d_cell_bounds(result.latitude, i, j)
            result.vertices_longitude[j, i] = _calculate_2d_cell_bounds(result.longitude, i, j)

    return result
