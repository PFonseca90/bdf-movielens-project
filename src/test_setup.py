import duckdb
import polars as pl
import pyarrow as pa
import pandas as pd
import matplotlib

print("DuckDB:", duckdb.__version__)
print("Polars:", pl.__version__)
print("PyArrow:", pa.__version__)
print("Pandas:", pd.__version__)
print("Matplotlib:", matplotlib.__version__)

print("\nSetup OK!")