# travel-helper

Python package providing utilities to estimate fares and plan trips.

## Installation

```bash
pip install .
```

## Usage

```python
from travel_helper import estimate_fare, estimate_trip

price = estimate_fare(distance_km=12.5, base_fare=3.0, per_km=1.8)
trip = estimate_trip(origin="Taipei 101", destination="Taoyuan Station")
```

## Development

Build and install locally:

```bash
pip install build
python -m build
pip install dist/travel_helper-0.1.0-py3-none-any.whl
```