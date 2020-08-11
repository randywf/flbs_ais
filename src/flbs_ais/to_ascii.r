#!/usr/bin/env Rscript
library(raster)

args = commandArgs(trailingOnly=TRUE)

if (length(args)==0) {
    stop("At least one argument must be supplied (input file).n", call.=FALSE)
} else if (length(args)==1) {
    fn <- args[1]
}

print(fn)

rs <- raster(fn)
nb <- nbands(rs)

for (i in 1:nb) {
    new_fn <- substr(fn, start=0, stop=nchar(fn)-4)
    new_fn <- paste(new_fn, "band", i, ".asc", sep="")
    print(new_fn)
    print("creating raster")
    rs_i <- raster(fn, band=i)
    #print("forming aggregate")
    #rs_ag <- aggregate(rs_i, fact=2)
    print("writing raster to ascii")
    writeRaster(rs, new_fn, format="ascii")
}
