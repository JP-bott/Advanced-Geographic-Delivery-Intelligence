# Geographic reference points

`city_centers.geojson` is a hand-curated set of representative Philippine city-center coordinates used to label the fictional delivery destinations. It is not an authoritative administrative boundary dataset and does not contain geocoded customer addresses.

The project uses city-point markers rather than inventing region polygons. There is no choropleth, and the geographic map requires no paid tiles or API keys. Plotly's bundled geo renderer provides a country-outline map after installation. The WGS84 geodesic length between hub and city-center points is explicitly **not a measured road distance**.
