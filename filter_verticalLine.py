#!/usr/bin/env python

# author: Bruno Combal
# date: November 2014
# replace a line of value with interpolated values

try:
    from osgeo import gdal
    from osgeo.gdalconst import *
    gdal.TermProgress = gdal.TermProgress_nocb
except ImportError:
    import gdal
    from gdalconst import *
 
try:
    import numpy as N
    N.arrayrange = N.arange
except ImportError:
    import Numeric as N
 
try:
    from osgeo import gdal_array as gdalnumeric
except ImportError:
    import gdalnumeric

import sys
import os

# ___________________________
def usage():
    text = 'Interpolate vertical lines in images dues to maps regridding boundaries disagreements.\n'
    text = text + 'SYNOPSIS:\n\t{0} -o outFile [-lowerBound float] [-upperBound float] [-of outformat] [-co formatOption]* (-lineDef int int)* infile'.format(__file__)
    text = text + '\tlineDef int int: the position (column) and width (in pixel) of the line to reprocess\t'
    
    return text
# ___________________________
def exitMessage(msg, exitCode='1'):
    print msg
    print
    print usage()
    sys.exit(exitCode)

# ___________________________
def nan_helper(y):
    """Helper to handle indices and logical indices of NaNs.

    Input:
        - y, 1d numpy array with possible NaNs
    Output:
        - nans, logical indices of NaNs
        - index, a function, with signature indices= index(logical_indices),
          to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    """

    return N.isnan(y), lambda z: z.nonzero()[0]
# _____________
def do_interpolate(infile, xposList, xwidthList, outfile, lowerBound, upperBound, fileFormat, formatOptions):
    # read data
    infid=gdal.Open(infile, GA_ReadOnly)
    data = infid.GetRasterBand(1).ReadAsArray(0, 0, infid.RasterXSize, infid.RasterYSize)

    # instantiate output array
    newData = N.copy(data)

    for (xpos, xwidth) in zip(xposList, xwidthList):

        xToReplace=[]
        for ii in range(xwidth): # create list of x position to replace
            xToReplace.append(xpos + ii)

        for iline in range(infid.RasterYSize):
            thisData = N.ravel(data[iline,:])
            # do we have data around the problem?
            before = thisData[xpos - 1]
            after = thisData[xpos + xwidth]
            if (before > lowerBound) and (before < upperBound) and (after > lowerBound) and (after < upperBound):
                newData[iline, xToReplace] = N.interp(xToReplace, [xpos-1, xpos+xwidth], [thisData[xpos-1], thisData[xpos+xwidth]])

    # write result
    outDrv = gdal.GetDriverByName(fileFormat)
    outDS = outDrv.Create(outfile, infid.RasterXSize, infid.RasterYSize, 1, GDT_Float32, formatOptions)
    outDS.GetRasterBand(1).WriteArray(newData, 0, 0)
    outDS.SetProjection( infid.GetProjection())
    outDS.SetGeoTransform( infid.GetGeoTransform() ) 
        
# _____________
if __name__=="__main__":

    infile=None #'/data/tmp/new_algo/tos_rcp85_forpublication/out/diff_decades_2050_2010_referenced.tif'
    outfile=None #'/data/tmp/new_algo/tos_rcp85_forpublication/out/interpolated_diff_decades_2050_2010.tif'
    xpos=[] #639
    xwidth=[] #2
    fileFormat='GTiff'
    formatOptions=[] #['compress=LZW']
    lowerBound=0
    upperBound=10

    ii = 1
    while ii < len(sys.argv):
        arg = sys.argv[ii].lower()
        if arg=='-o':
            ii = ii + 1
            outfile = sys.argv[ii]
        elif arg=='-lowerbound':
            ii = ii + 1
            lowerBound = float(sys.argv[ii])
        elif arg=='-upperbound':
            ii = ii + 1
            upperBand = float(sys.argv[ii])
        elif arg=='-co':
            ii = ii + 1
            formatOptions.append(sys.argv[ii])
        elif arg=='-of':
            ii = ii + 1
            fileFormat=sys.argv[ii]
        elif arg=='-linedef':
            ii = ii + 1
            xpos.append(int(sys.argv[ii]))
            ii = ii + 1
            xwidth.append(int(sys.argv[ii]))
        else:
            infile=sys.argv[ii]
        ii = ii + 1

    # check parameters
    if infile is None:
        exitMessage('Please define an input file name. Exit(1)', 1);
    if outfile is None:
        exitMessage('Please define an output file name, use option -o. Exit(2)', 2);
    if len(xpos)==0:
        exitMessage('Missing position(s), use option -xpos. Exit(3)',3)
    if len(xwidth)==0:
        exitMessage('Missing width(s), use option -xwidth. Exit(4)',4)
    if len(xpos) != len(xwidth):
        exitMessage('xpos and xwidth arrays must have the same lengths. Exit(5).', 5)

    if not os.path.exists(infile):
        exitMessage('Input file {0} does not exist. Exit(6).'.format(infile),6)

    # all ok, call the processing 
    do_interpolate(infile, xpos, xwidth, outfile, lowerBound, upperBound, fileFormat, formatOptions)

# end of script
    
