from tempfile import NamedTemporaryFile
from typing import Any

from pathlib import Path
import pandas as pd


def validate_file_exist(path:Path, label:str = "File"):
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    
    if not path.is_file():
        raise ValueError(f"{label} is not a file: {path}")


def write_csv_atomic(
    dataframe: pd.DataFrame,
    output_path: Path,
    **to_csv_kwargs: Any,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok = True)
    encoding = str(to_csv_kwargs.pop("encoding", "utf-8"))
    with NamedTemporaryFile(
        mode = "w",
        suffix = ".csv",
        dir= output_path.parent,
        delete= False,
        newline = '',
        encoding=encoding,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)

    try:
        dataframe.to_csv(
            temporary_path,
            index=False,
            encoding=encoding,
            **to_csv_kwargs,
        )
        temporary_path.replace(output_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    

