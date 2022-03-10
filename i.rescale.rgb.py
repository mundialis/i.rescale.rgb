#!/usr/bin/env python3
#
############################################################################
#
# MODULE:      i.reclass.rgb
# AUTHOR(S):   Guido Riembauer, <riembauer at mundialis.de>
#
# PURPOSE:     Rescales raster values for optimized RGB visualization
# COPYRIGHT:   (C) 2020-2022 by mundialis GmbH & Co. KG and the GRASS Development Team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
#############################################################################

# %Module
# % description: Rescales raster values for optimized RGB visualization.
# % keyword: raster
# % keyword: RGB
# % keyword: satellite
# % keyword: colors
# %End

# %option G_OPT_R_INPUT
# % key: red
# % label: Name raster for red channel
# %end

# %option G_OPT_R_INPUT
# % key: green
# % label: Name raster for green channel
# %end

# %option G_OPT_R_INPUT
# % key: blue
# % label: Name raster for blue channel
# %end

# %option G_OPT_OUTPUT
# % key: output
# % required: yes
# % label: Name of output group
# %end

# %option
# % key: lower_percentile
# % type: integer
# % label: Lower percentile for raster reclassification (percent)
# % options: 1-100
# % answer: 2
# %end

# %option
# % key: upper_percentile
# % type: integer
# % label: Upper percentile for raster reclassification (percent)
# % options: 1-100
# % answer: 98
# %end

# %option
# % key: output_range
# % type: string
# % label: Output raster value range in format <min,max>
# % answer: 0,255
# %end

# %option
# % key: suffix
# % type: string
# % label: Suffix to be added to each reclassified raster (added with underscore)
# % answer: reclassified
# %end

# %flag
# % key: f
# % description: Allow floating point values in output rasters (default is integer)
# %end


import grass.script as grass
import os
import atexit

rm_rasters = []


def cleanup():
    nuldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nuldev}
    for rmrast in rm_rasters:
        if grass.find_file(name=rmrast, element="raster")["file"]:
            grass.run_command("g.remove", type="raster", name=rmrast, **kwargs)


def main():
    global rm_rasters
    red = options["red"]
    green = options["green"]
    blue = options["blue"]
    lower_percentile = options["lower_percentile"]
    upper_percentile = options["upper_percentile"]
    suffix = options["suffix"]
    output = options["output"]
    output_range = options["output_range"].split(",")

    rgb_in = [red, green, blue]
    if len(set(rgb_in)) < 2:
        grass.fatal(_("At least two different rasters must be used as input."))

    # check if the desired output range makes sense
    try:
        lower_out = output_range[0]
        upper_out = output_range[1]
        lower_out_int = int(lower_out)
        upper_out_int = int(upper_out)
        if upper_out_int < lower_out_int:
            grass.fatal(
                _("First value of output_range (%s) is larger than second value (%s)")
                % (lower_out_int, upper_out_int)
            )
    except Exception:
        grass.fatal(
            _(
                "Parameter output_range must be in format <min,max> where min and max "
                "are integer values"
            )
        )

    # rasters to be reclassified
    reclassified_rasters = []
    for rast in rgb_in:
        rescaled_rast = "%s_%s" % (rast, suffix)
        if rescaled_rast not in reclassified_rasters:
            vals = list(
                grass.parse_command(
                    "r.quantile",
                    input=rast,
                    percentiles="%s,%s" % (lower_percentile, upper_percentile),
                    quiet=True,
                ).keys()
            )
            lower_in = vals[0].split(":")[-1]
            upper_in = vals[1].split(":")[-1]
            # assign min/max in value to pixels that would become null otherwise
            temp_mapcalc_rast = "%s_tmp_%s" % (rast, os.getpid())
            rm_rasters.append(temp_mapcalc_rast)
            expression = (
                "%(out)s = if(%(in)s <= %(lower_in)s, %(lower_in)s,"
                "if(%(in)s >= %(upper_in)s, %(upper_in)s,"
                "%(in)s))"
                % {
                    "out": temp_mapcalc_rast,
                    "in": rast,
                    "lower_in": lower_in,
                    "upper_in": upper_in,
                }
            )
            grass.run_command("r.mapcalc", expression=expression, quiet=True)
            # rescaling
            resc_expression2 = (
                "((%(in)s - %(lower_in)s)/"
                "(%(upper_in)s - %(lower_in)s))"
                " * %(upper_out)s + %(lower_out)s"
                % {
                    "in": temp_mapcalc_rast,
                    "lower_in": lower_in,
                    "upper_in": upper_in,
                    "upper_out": upper_out,
                    "lower_out": lower_out,
                }
            )
            if flags["f"]:
                resc_expression_part2 = resc_expression2
            else:
                resc_expression_part2 = "round(%s)" % resc_expression2

            resc_expression = " = ".join([rescaled_rast, resc_expression_part2])
            grass.run_command("r.mapcalc", expression=resc_expression, quiet=True)

        reclassified_rasters.append(rescaled_rast)

    # the length of this set should only be 2 or 3
    if len(set(reclassified_rasters)) == 2:
        unique_rasters = []
        dupl_index = None
        # find duplicate
        for idx, val in enumerate(reclassified_rasters):
            if val not in unique_rasters:
                unique_rasters.append(val)
            else:
                # there can be maximum one duplication
                dupl_index = idx
        dupl_raster = reclassified_rasters[dupl_index]
        dupl_rast_copied = "%s_copied" % dupl_raster
        grass.run_command(
            "g.copy", raster="%s,%s" % (dupl_raster, dupl_rast_copied), quiet=True
        )
        reclassified_rasters[dupl_index] = dupl_rast_copied

    # create the group
    grass.run_command("i.group", group=output, input=reclassified_rasters, quiet=True)
    grass.message(_("Created output group <%s>") % output)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
