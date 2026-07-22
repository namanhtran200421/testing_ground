from pathlib import Path
import pandas as pd
from tempfile import NamedTemporaryFile


def validate_file_exist(path:Path, label:str = "File"):
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    
    if not path.is_file():
        raise ValueError(f"{label} is not a file: {path}")


def write_csv_atomic(dataframe: pd.DataFrame, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok = True)
    with NamedTemporaryFile(
        mode = "w",
        suffix = ".csv",
        dir= output_path.parent,
        delete= False,
        newline = '',
        encoding='utf-8',
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)

    try:
        dataframe.to_csv(temporary_path, index=False)
        temporary_path.replace(output_path)
    except Exception as error:
        print(error)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    


