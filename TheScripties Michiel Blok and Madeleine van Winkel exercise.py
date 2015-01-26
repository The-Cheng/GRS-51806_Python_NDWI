# Michiel Blok and Madeleine van Winkel
# 23 January 2015

# Import modules
import os, numpy,  osr
import requests
import tarfile
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly, GDT_Float32

# Download data
def downloadData():
    # Create directories
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('results'):
        os.makedirs('results')

    # Define variables and paths
    landsat_url = 'https://www.dropbox.com/s/zb7nrla6fqi1mq4/LC81980242014260-SC20150123044700.tar.gz?dl=1'
    landsat_dl = 'downloads/LC81980242014260-SC20150123044700.tar'

    r = requests.get(landsat_url)
    file_out = open(landsat_dl, 'wb')
    file_out.write(r.content)
    file_out.close()

# Extract data
def extractData():
    landsat_tar = tarfile.open(landsat_dl)
    landsat_tar.extractall('data')
    landsat_tar.close()

# Load Landsat data
def openData():
    bands = ['band4', 'band5']
    for i in range(len(bands)):
        datafile = '/home/user/Git/Python/LC81980242014260LGN00_sr_%s.tif' % bands[i]
        dataSource = gdal.Open(datafile, GA_ReadOnly)
        array = dataSource.GetRasterBand(1).ReadAsArray(0, 0, dataSource.RasterXSize, dataSource.RasterYSize)
        bands[i] = array.astype(numpy.float32)
    return bands,  dataSource

# Calculate NDWI
def NDWI(band4,  band5):
    mask = numpy.greater(band4 + band5, 0)
    NDWI = numpy.choose(mask, (-99, (band4 - band5) / (band4 + band5)))
    return NDWI

# Create coordinate transformation
def reproject(NDWI):
    # Spatial Reference System
    inputEPSG = 4326
    outputEPSG = 28992
    
    inSpatialRef = osr.SpatialReference()
    inSpatialRef.ImportFromEPSG(inputEPSG)
    
    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(outputEPSG)
    
    coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
    
    # Transform NDWI
    NDWI.Transform(coordTransform)
    return NDWI

# Write data to output file
def createOutput(NDWI,  dataSource):
    driver = gdal.GetDriverByName('GTiff')
    outData = driver.Create('/home/user/Git/Python/NDWI.tif', dataSource.RasterXSize, dataSource.RasterYSize, 1, GDT_Float32)
    outNDWI = outData.GetRasterBand(1)
    outNDWI.WriteArray(NDWI, 0, 0)
    outNDWI.SetNoDataValue(-99)
    return outNDWI, outData

# Flush the memory
def flush(outNDWI, outData):
    outNDWI.FlushCache()
    outData.FlushCache()


if __name__ == '__main__':
    # Download and extract the data
    downloadData()
    extractData()

    # Opening the data
    bands, dataSource = openData()

    # Derive the NDWI from the landsat image
    NDWI = NDWI(bands[0], bands[1])
    
    # Reproject the image from Lat/Long WGS84 (x.ImportFromEPSG(4326)) to Amersfoort / RD_New (x.ImportFromEPSG(28992))
    #NDWI = reproject(NDWI)
    
    # Save the result
    outNDWI, outData = createOutput(NDWI,  dataSource)
    flush(outNDWI, outData)
