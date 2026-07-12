## DESCRIPTION

*i.rescale.rgb* is a GRASS addon that works similar to
[i.colors.enhance](i.colors.enhance.md) but changes and rescales the
actual raster values and not the corresponding color table. This is only
useful for visualization purposes outside of GRASS GIS. The created
group can be used as **r.out.gdal** input parameter for the multi-band
export.

## EXAMPLES

Optimize the raster values of three input bands for RGB visualization;
enhance contrast by limiting input data to the area between the 2% and
98% percentile:

```sh
i.rescale.rgb red=red_channel green=green_channel blue=blue_channel output=output_group lower_percentile=2 upper_percentile=98
```

In case of export to Byte type with no-data (NULL) values being present,
the way to go is rescaling to 0..254 range (rather than the default
0..255 range):

```sh
i.rescale.rgb red=red_channel green=green_channel blue=blue_channel output=output_group output_range=0,254 lower_percentile=2 upper_percentile=98
```

## SEE ALSO

*[r.mapcalc](r.mapcalc.md), [i.colors.enhance](i.colors.enhance.md)*

## AUTHOR

Guido Riembauer, [mundialis](https://www.mundialis.de/)
