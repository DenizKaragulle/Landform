#-------------------------------------------------------------------------------
# Name:        PLAIN 30 M DATA, 5CELL
# Purpose:
#
# Author:      deni6533
#
# Created:     28/01/2015
# Copyright:   (c) deni6533 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.env.cellSize = "MINOF"

#Parameters

# 30 meter resolution DEM with 8% slope threshold (Closest to Hammond and USGS models, but hills are underestimated...
##DEM_Res = 30
##Slope_Reclass_Size = 5
##Plains_Nbrhd = 5
##Mtns_Nbrhd = 50

# 30 meter resolution DEM with 5% slope threshold (Attempting to properly estimate hills...
DEM_Res = 30
Slope_Reclass_Size = 5
Plains_Nbrhd = 5
Mtns_Nbrhd = 50

##Dem_Res = 250
##Slope_Reclass_Size =

#Workspace
fc=r"D:\LandForms\Utah\Input.gdb\GrandCanyon_NED30_eq"
out_fc=r"D:\LandForms\Utah\Plains13.gdb"
outputstif=r"D:\LandForms\Tif"

env.workspace= r"D:\LandForms\Utah\Plains13.gdb"
scratchWorkspace= r"C:\scratch\scratch\scratch.gdb"
arcpy.env.overwriteOutput = 'True'
# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")
#-----------------------------------------------------------------------
#(slope)Calculate slope from NED (prcntg)
slope=Slope(fc,"PERCENT_RISE")
slope.save(out_fc + "\slope")

#focal statistics
slope_neigh= NbrRectangle(Plains_Nbrhd, Plains_Nbrhd, "CELL")
slope_sum= FocalStatistics(slope, slope_neigh, "SUM", "")
slope_sum.save(out_fc + "\slope_sum")

#add message
arcpy.AddMessage("Running script reclassifiying slope...")
#(reclass_slope) Reclassify Slope, Slope categories map
#areas greater than Slope_Reclass_Size slope less than Slope_Reclass_Size
maxslope=arcpy.GetRasterProperties_management(slope_sum, "MAXIMUM")
minslope=arcpy.GetRasterProperties_management(slope_sum, "MINIMUM")

reclass_slopeRange=RemapRange([[minslope, Slope_Reclass_Size, 0],[Slope_Reclass_Size, maxslope, 1]])
reclass_slope=Reclassify(slope, "value", reclass_slopeRange,"NODATA")
reclass_slope.save(outputstif+"\slopereclass.tif")

#majority filTER
majorityslope=MajorityFilter(reclass_slope, "EIGHT", "MAJORITY")
majorityslope.save(out_fc + "\majorityslope")

#(reclass_slope_sum) Run the sum focal stat. of the slope categories map
neighborhood6= NbrRectangle(Plains_Nbrhd, Plains_Nbrhd, "CELL")
reclass_slope_sum= FocalStatistics(majorityslope, neighborhood6, "SUM", "")



#(slope_sum_reclass) Reclassify the percent of near level land
#*Hammond's slope parameter map
slope_sum_reclass_range=RemapRange([[0, 5, 1],[5, 25, 2]])
slope_sum_reclass=Reclassify(reclass_slope_sum, "value", slope_sum_reclass_range,"NODATA")
slope_sum_reclass.save(out_fc + "\slope_sum_reclass")


#(reclass_slope_std) Run the std dev of the slope categories
reclass_slope_std_neigh= NbrRectangle(Plains_Nbrhd, Plains_Nbrhd, "CELL")
reclass_slope_std= FocalStatistics(slope, reclass_slope_std_neigh, "STD", "")
#reclass_slope_std.save(out_fc+"\reclass_slope_std")


#(std_reclass) Reclassify the std dev of slope map
std_reclass_range=RemapRange([[0, 2, 10],[2, 5, 20] , [5, 304, 30]])
std_reclass=Reclassify(reclass_slope_std, "value", std_reclass_range,"NODATA")
std_reclass.save(out_fc + "\std_reclass")

#add message
arcpy.AddMessage("Calculating slope parameter...")

#adding std slope map and sum of cells map to find slope
slope_std_sum= (arcpy.Raster(out_fc + "\std_reclass")) + (arcpy.Raster(out_fc + "\slope_sum_reclass"))
slope_std_sum.save(out_fc + "\slope_std_sum")


#reclassify slope map to find the finla slope map
slope_remap=RemapValue([[11, 100], [12, "NODATA"], [21, 200], [22, "NODATA"] , [31, 300], [32, "NODATA"]])
slopefinal=Reclassify(slope_std_sum, "Value", slope_remap)

slopefinal.save(out_fc + "\slopefinal3")

print "SLOPE PARAMETER MODEL DONE"
#----------------------------------------------------------------
#HAMMOND'S RELIEF PARAMETER MODEL
#add message
arcpy.AddMessage("Calculating Hammond's relief parameter model...")
#(max_elevation) Determine the maximum NED value
#within a 20 pixel circular window
max_elevation_neigh= NbrRectangle(Plains_Nbrhd, Plains_Nbrhd, "CELL")
max_elevation= FocalStatistics(fc, max_elevation_neigh, "MAXIMUM", "")
max_elevation.save(out_fc + "\max_elevation")

maxelv=arcpy.Raster(out_fc+"\max_elevation")

#(min_elevation) Determine the minimum NED value
#within a 20 pixel circulor window
min_elevation_neigh= NbrRectangle(Plains_Nbrhd, Plains_Nbrhd, "CELL")
min_elevation= FocalStatistics(fc, min_elevation_neigh, "MINIMUM", "")
min_elevation.save(out_fc + "\min_elevation")
minelv=arcpy.Raster(out_fc + "\min_elevation")

#add message
arcpy.AddMessage("Creating a relief map...")
#(diffeence) Create a relief map (maximum elevation - minimum elevation)

difference= maxelv - minelv
difference.save(out_fc+"\difference")

#add message
arcpy.AddMessage("Reclassifiying the relief map...")
#(MAP12) Reclassify the relief map
#*Hammond's relief parameter map
relief_range=RemapRange([[0, 3, 10],[3, 9, 20], [9, 676, "NODATA"]])
reliefoutput=Reclassify(difference, "Value", relief_range,"NODATA")
reliefoutput.save(r"D:\LandForms\Tif\reliefouttttput5.tif")

print " RELIEF PARAMETER MODEL DONE"

#----------------------------------------------------------------
# LANDFORM CLASSIFICATION
#add message
arcpy.AddMessage("Calculating landform classification...")
#add message
arcpy.AddMessage("Creating Hammond's landform raster...")
#(profile20)Hammond terrain type code (map8+map12)
profile20= (arcpy.Raster(out_fc + "\slopefinal3")) + (arcpy.Raster(r"D:\LandForms\Tif\reliefouttttput5.tif"))
profile20.save(out_fc + "\profile20")


print "reclassifiying map33..."
#(reclassify_profile20) reclassify map33
#230 empty values they are gentle slope in uplands %0 %gentle slope

reclass_profile20_range=RemapRange([[110, 114, 1], [120, 124, 2 ], [210, 214, 3], [220, 224, 2], [310, 314, 4], [320, 324, 5]])
reclass_profile20=Reclassify(profile20, "Value", reclass_profile20_range,"NODATA")
reclass_profile20.save(r"D:\LandForms\Utah\finalmap4plain.tif")

#(MAP35) Focal Stats, input map34, 5X5 cell, rectangle, majority
reclass_profile20_neigh= NbrRectangle(Plains_Nbrhd, Plains_Nbrhd, "CELL")
FinalMap= FocalStatistics(reclass_profile20, reclass_profile20_neigh, "MAJORITY", "")
FinalMap.save(out_fc+"/FinalMap")


#Add a labels field to the attribute table for FinalMap to and type in labels
fieldlength = 1050
FinalMap_1=arcpy.AddField_management (out_fc + "\FinalMap", "Labels", "TEXT", "","", fieldlength)

#Add Labels to the field
fields= ["Value","Labels"]
with arcpy.da.UpdateCursor(FinalMap_1, fields) as cursor:
    for row in cursor:
        if row[0] == 1:
            row[1] = "Plains"
        elif row[0] == 2 :
            row[1] = "Smooth plains with some local relief"
        elif row[0] == 3 :
            row[1] = "Flat plains might have some noise"
        elif row[0] == 4 :
            row[1] = "Irregular Plains"
        elif row[0] == 5 :
            row[1] = "Badlands"


        cursor.updateRow(row)

#reclassify for only plains rest of them is no data
reclass_finalmap=RemapValue([[1, 1], [2, 1 ], [3, "NODATA"], [4, "NODATA"], [5, "NODATA"]])
reclass_profile20=Reclassify(FinalMap_1, "Value", reclass_finalmap,"NODATA")
reclass_profile20.save(r"D:\LandForms\Utah\reclass_flats.tif")
#shrink with 1 cell
outshrink=Shrink((arcpy.Raster(r"D:\LandForms\Utah\reclass_flats.tif")), 1, [1])
outshrink.save(r"D:\LandForms\Utah\shrink_flats.tif")
#expand with 1 cell
outexpand=Expand ((arcpy.Raster(r"D:\LandForms\Utah\shrink_flats.tif")), 1, [1])
outexpand.save(r"D:\LandForms\Utah\expand_flats.tif")

reclass_finalmap_2=RemapValue([[1, 1]])
reclass_profile20=Reclassify( arcpy.Raster(r"D:\LandForms\Utah\expand_flats.tif"), "Value", reclass_finalmap_2,"NODATA")
reclass_profile20.save(r"D:\LandForms\Utah\final_Flats.tif")
