# syntheticus_connect
## Overview

SyntheticusConnect is a Python client for Syntheticus, designed to make interactions with the Syntheticus service easier and more Pythonic.

## Installation

Install SyntheticusConnect with pip:

pip install SyntheticusConnect

## Usage

Import the package and create a new `SyntheticusConnect` object:

```python
from SyntheticusConnect import SyntheticusConnect

syntheticus = SyntheticusConnect(base_url="http://your_base_url.com", username="your_username", password="your_password")

# Get a specific model
dag = syntheticus.get_dag("dag_id")

# List all models
syntheticus.list_models()

# Trigger a synthetization process
syntheticus.synthetize("dag_id", "run_id", "project_name")
