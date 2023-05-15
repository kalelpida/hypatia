# SatViz: Satellite Visualization

SatViz is a Cesium-based visualization pipeline to generate interactive
satellite network visualizations. It makes use of the online Cesium API
by generating CesiumJS code. The API calls require its user to obtain 
a Cesium access token (via [https://cesium.com/]()).

## Getting started

1. Obtain a Cesium access token at [https://cesium.com/]()

2. Edit `static_html/top.html`, and insert your Cesium access 
   token at line 10:

   ```javascript
   Cesium.Ion.defaultAccessToken = '<CESIUM_ACCESS_TOKEN>';
   ```

3. Now you are able to make use of the scripts in `scripts/`


## Script description

1. `visualize_constellation.py`: Generates visualizations for entire constellation (multiple shells).

2. `visualize_horizon_over_time.py`: Finds satellite positions (azimuth, altitude) over time for a static observer and plots them relative to the observer.

3. `visualize_path.py`: Visualizes paths between pairs of endpoints at specific time instances.

4. `visualize_path_no_isl.py`: Visualizes paths between pairs of endpoints when no inter-satellite connectivity exists.

5. `visualize_path_wise_utilization.py`: Visualizes link utilization for specific end-end paths at a specific time instance.

6. `visualize_utilization.py`: Visualizes link utilization for all end-end paths at a specific time instance.

Among above scripts, `visualize_utilization.py` and `visualize_path.py` have been updated. The first can be called on a directory, while the latter can be called using `visualize_multipath.sh`, others may not work as expected. 