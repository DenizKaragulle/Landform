#-------------------------------------------------------------------------------
# Name:        Developing Landform Maps implementing Hammonds Model
# Author:      Deniz Basaran
# Created:     24/11/2014
# Copyright:   (c) deni6533 2014
#-------------------------------------------------------------------------------
import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.env.cellSize = "MINOF"

#Workspace
fc=r"D:\LandForms\OffshoreWater\world_elevation_GMTED_equidistant.tif"
out_fc=r"D:\LandForms\OffshoreWater\world_250.gdb"


env.workspace=r"D:\LandForms\Boston"

arcpy.env.overwriteOutput = 'True'
# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")



#-------------------------------------------------------------------------------
#SLOPE PARAMETER MODEL
#add message
arcpy.AddMessage("Calculating slope parameter model...")
#add message
arcpy.AddMessage("Reclassifiying NED to figure out all non zero elevations...")
#(MAP1)reclassify map1, to figure out all non zero elevations.
remap= RemapRange([[0.1,1050,1]])
map1=Reclassify(fc, "value", remap, "NODATA")
map1.save(out_fc + "\map1")


#(MAP2)determine the number of cells within the 20 pixel radius circular window,
#this step will be use later in percentage calculations
neighborhood= NbrCircle(20,"CELL")
map2=FocalStatistics(map1, neighborhood, "SUM", "")
map2.save(out_fc + "\map2")

#(MAP3)creating a float point version of Map2,
#this map will be used later in the model for
#calculation of percentages within the 20 pixel radius circular window.
map3=Float(map2)
map3.save(out_fc + "\map3")



###determine offshore
##
##Offshore_1=Reclassify(offshore, "Value","1 -1;2 -1;5 -1;6 -1;7 -1;8 -1")
##Offshore_1.save(out_fc+"\offshore222")

#add message
arcpy.AddMessage("Running script create slope...")
#(MAP4)Calculate slope from NED (prcntg)
map4=Slope(fc,"PERCENT_RISE")
map4.save(out_fc + "\map4")

#add message
arcpy.AddMessage("Running script reclassifiying slope...")
#(MAP5) Reclassify Slope, Slope categories map
#areas greater than 8% slope less than 8%
maxslope=arcpy.GetRasterProperties_management(map4, "MAXIMUM")
minslope=arcpy.GetRasterProperties_management(map4, "MINIMUM")

remap2=RemapRange([[minslope, 8, 0],[8, maxslope, 1]])
map5=Reclassify(map4, "value", remap2,"NODATA")
map5.save(out_fc + "\map5")
#if x>=8:
#     x=0
#if x<8:
#   x=1


#(MAP6) Run the sum focal stat. of the slope categories map(map5)
#within a 1.5 km circulor window
neighborhood6= NbrRectangle("50", "50", "CELL")
map6= FocalStatistics(map5, neighborhood6, "SUM", "")
map6.save(out_fc + "\map6")

#add message
arcpy.AddMessage("Calculating % near level land...")
#(MAP7) Calculate the % near level land
#make temporary layer from map5
map5_1=arcpy.MakeRasterLayer_management (map5, "map5_1")
totalCount= 0
nearLevel = 0
with arcpy.da.SearchCursor(map5_1, ["VALUE", "COUNT"]) as cursor:
    for row in cursor:
        totalCount = totalCount +row[1]
        if row[0] == 0:
            nearLevel = row[1]
    map7= (float(nearLevel)/float(totalCount)) *100


#(MAP8) Reclassify the percent of near level land
#*Hammond's slope parameter map
remap8=RemapRange([[0, 500, 400],[500, 1250, 300],[1250, 2000, 200], [2000, 2500, 100]])
map8=Reclassify(map6, "value", remap8,"NODATA")
map8.save(out_fc + "\map8")

print "SLOPE PARAMETER MODEL DONE"
#-------------------------------------------------------------------------------
#HAMMOND'S RELIEF PARAMETER MODEL
#add message
arcpy.AddMessage("Calculating Hammond's relief parameter model...")
#(MAP9) Determine the maximum NED value
#within a 20 pixel circular window
neighborhood7= NbrRectangle("50", "50", "CELL")
map9= FocalStatistics(fc, neighborhood7, "MAXIMUM", "")
map9.save(out_fc + "\map9")

max=arcpy.Raster(out_fc+"\map9")

#(MAP10) Determine the minimum NED value
#within a 20 pixel circulor window
neighborhood8= NbrRectangle("50", "50", "CELL")
map10= FocalStatistics(fc, neighborhood8, "MINIMUM", "")
map10.save(out_fc + "\map10")
min=arcpy.Raster(out_fc + "\map10")

#add message
arcpy.AddMessage("Creating a relief map...")
#(MAP11) Create a relief map (map9-map10)

map11= max - min
map11.save(out_fc+"\map11")

#add message
arcpy.AddMessage("Reclassifiying the relief map...")
#(MAP12) Reclassify the relief map
#*Hammond's relief parameter map
remap12=RemapRange([[0, 30, 10],[30, 90, 20],[90, 150, 30], [150, 300, 40], [300, 900, 50], [900, 99999, 60]])
map12=Reclassify(map11, "value", remap12,"NODATA")
map12.save(out_fc + "\map12")

print "HAMMOND'S RELIEF PARAMETER MODEL DONE"
#-------------------------------------------------------------------------------
#PROFILE SUB MODEL
#add message
arcpy.AddMessage("Calculating profile parameter...")

#(MAP13) Create local relief differences map,(map11/2)
#calculate one half of the maximum relief in the 20 pixel circulor window

map13=(arcpy.Raster(out_fc+"\map11")) / 2
map13.save(out_fc + "\map13")

#(MAP14) Create profile value map, (map10+map13)
map14= (arcpy.Raster(out_fc + "\map10")) + (arcpy.Raster(out_fc + "\map13"))
map14.save(out_fc + "\map14")

#(MAP15)determine upland and lowland map ( map14-NED)
# pixel values less than 0 represent upland areas;
#pixel values greater than 0 represent lowland values

map15 = (arcpy.Raster(out_fc + "\map14")) - (arcpy.Raster(fc))
map15.save(out_fc + "\map15")

#(MAP16) Profile Type map, Reclassify upland and lowland
#!!!!!!find the maximum values and minimum values for map15!!!!!!!!!
# if x>0: (lowland)
#    x=1
#if x<0: (upland)
#   x=2
maximumv=arcpy.GetRasterProperties_management(map15, "MAXIMUM")
minimumv=arcpy.GetRasterProperties_management(map15, "MINIMUM")

remap16=RemapRange([[0, maximumv, 1],[minimumv, 0, 2]])
map16=Reclassify(map15, "value", remap16,"NODATA")
map16.save(out_fc + "\map16")
print "working map 17..."
#add message
arcpy.AddMessage("Creating lowlands map...")
#(MAP17) Lowlands Map,reclassify profile type map
# if y=1: (lowland)
#   y=1
#if y=2: (upland)
#   y=0
remap17=RemapValue([[1, 1],[2, 0]])
map17=Reclassify(map16, "value", remap17,"NODATA")
map17.save(out_fc + "\map17")

#add message
arcpy.AddMessage("Identifying gentle slopes")
#(MAP18) Identify gentle slopes, by identifying slopes less than 8 in lowlands,
#(map5*map17)
map18= (arcpy.Raster(out_fc + "\map17") * arcpy.Raster(out_fc + "\map5"))
map18.save(out_fc + "\map18")

#(MAP19) Determine the sum of the gentle slopes
#in lowlands map within a 20 pixel circular window (focal stat(sum) on map18)
neighborhood19= NbrRectangle("50", "50", "CELL")
map19= FocalStatistics(map18, neighborhood19, "SUM", "")
map19.save(out_fc + "\map19")


#(MAP20) create the floating point version of Map6 via Map Algebra Float
#this map represent the sum of the gentle slopes within a 20 pixel circular window,
#this map is for the percentage calculation in the following steps.
map20=Float(map6)
map20.save(out_fc + "\map20")

#add message
arcpy.AddMessage("Calculate the percentage of gentle slopes in lowlands...")
#(MAP21)calculate the percentage of gentle slopes in lowlands, (map19/map20)
map21=arcpy.Raster(out_fc + "\map19") / arcpy.Raster(out_fc + "\map20")
map21.save(out_fc + "\map21")

#(Map21_1) reclassify for no data values
remap21_1=RemapRange([[0, 1, 1000],["NODATA", 0]])
map21_1=Reclassify(map21, "value", remap21_1)
map21_1.save(out_fc +"\map21_1")
#local stat min to get the map21
map21_orgn=CellStatistics ([map21, map21_1], "MINIMUM")
map21_orgn.save(out_fc+"\map21_orgn")

#(MAP22) isolate gentle slopes in lowlands. (map17*map21)
map22= (arcpy.Raster(out_fc + "\map17")) * (arcpy.Raster(out_fc + "\map21_orgn"))
map22.save(out_fc + "\map22")

print "working on map 23..."
#(MAP23) reclassify pecentage of gentle slopes
#0 0.00%
#2 0.50-0.75%
#1 0.75-1%
remap23=RemapRange([[0, 0.5, 0],[0.5, 0.75, 2],[0.75 , 1 , 1]])
map23=Reclassify(map22, "value", remap23,"NODATA")
map23.save(out_fc + "\map23")

#(MAP24)UPLANDs map, reclassify profile type map (map16)
#0    1(lowland)
#1    2(upland)
remap24=RemapValue([[1, 0],[2, 1]])
map24=Reclassify(map16, "value", remap24,"NODATA")
map24.save(out_fc + "\map24")

#(MAP25) identify gentle slopes, (map5*map24)
map25=(arcpy.Raster(out_fc + "\map5")) * (arcpy.Raster(out_fc + "\map24"))
map25.save(out_fc+ " \map25")

#(MAP26) sum (focal statistics) of the gentle slopes in lowlands map with in a 20 pixel circular window
#focal stat on map 25
neighborhood26= NbrRectangle("50", "50", "CELL")
map26= FocalStatistics(map25, neighborhood26, "SUM", "")
map26.save(out_fc + "\map26")
print"done map26 check results///!"
#add message
arcpy.AddMessage("Calculate the percentage of gentle slopes in uplands...")
#(MAP27) calculate percentage of gentle slopes in uplands (map26/map20)
map27=(arcpy.Raster(out_fc + "\map26"))/(arcpy.Raster(out_fc + "\map20"))
map27.save(out_fc + "\map27")

#(Map27_1) reclassify for no data values
remap27_1=RemapRange([[0, 1, 1000],["NODATA", 0]])
map27_1=Reclassify(map27, "value", remap27_1)
map27_1.save(out_fc +"\map27_1")
#local stat min to get the map21
map27_orgn=CellStatistics ([map27, map27_1], "MINIMUM")
map27_orgn.save(out_fc+"\map27_orgn")

#(MAP28) mask any uplands pixels from the gentle slopes in uplands map (map27*map24)
map28= (arcpy.Raster(out_fc + "\map27_orgn"))*(arcpy.Raster(out_fc + "\map24"))
map28.save(out_fc + "\map28")

print "working on map 29..."
#(MAP29) reclassify percentage of gentle slopes in uplands
#0  0.00%
#3  0.50-0.75%
#4  0.75-1.00%
remap29=RemapRange([[0, 0.5, 0],[0.5, 0.75, 3],[0.75 , 1 , 4]])
map29=Reclassify(map28, "value", remap29,"NODATA")
map29.save(out_fc + "\map29")

#(MAP30) Hammonds profile paramiter map (map23+map29)
map30=(arcpy.Raster(out_fc + "\map23")) + (arcpy.Raster(out_fc + "\map29"))
map30.save(out_fc + "\map30")

#(MAP31) adjusted profile parameter map, Reclassify hammons profile map (map30)
#1  0
remap31=RemapValue([[0, 1],[1,1],[2,2],[3,3],[4,4]])
map31=Reclassify(map30, "value", remap31,"NODATA")
map31.save(out_fc + "\map31")

print "PROFILE SUB MODEL DONE"
#-------------------------------------------------------------------------------
# LANDFORM CLASSIFICATION
#add message
arcpy.AddMessage("Calculating landform classification...")
#add message
arcpy.AddMessage("Creating Hammond's landform raster...")
#(MAP32)Hammond terrain type code (map8+map12)
map32= (arcpy.Raster(out_fc + "\map8")) + (arcpy.Raster(out_fc + "\map12"))
map32.save(out_fc + "\map32")

#(MAP33) final code (map32+map31)
map33= (arcpy.Raster(out_fc + "\map32")) + (arcpy.Raster(out_fc + "\map31"))
map33.save(out_fc + "\map33")



print "reclassifiying map33..."
#(MAP34) reclassify map33
#230 empty values they are gentle slope in uplands %0 %gentle slope

remap34=RemapRange([[111, 114, 51], [121, 124, 52], [131, 134, 53], [141, 144, 54], [151, 154, 55], [161, 164, 56], [211, 214, 41], [221, 224, 42], [231, 234, 43], [241, 244, 44], [251, 254, 45], [261, 264, 46], [311, 312, 13], [321, 324, 14], [331,332, 31], [333, 334, 21], [341, 342, 32], [343, 344, 22], [351, 352, 33], [353, 354, 23], [361,362, 34], [363, 364, 24], [411, 414, 11], [421, 424, 12], [431, 432, 31], [433, 434, 21], [441, 442, 32], [443, 444, 22], [451, 452, 33], [453, 454, 23], [461,462, 34], [463, 464, 24]])
map34=Reclassify(map33, "Value", remap34,"NODATA")
map34.save(out_fc + "\map34")

#(MAP35) Focal Stats, input map34, 5X5 cell, rectangle, majority
neighborhood6= NbrRectangle("5", "5", "CELL")
map35= FocalStatistics(map34, neighborhood6, "MAJORITY", "")
map35.save(out_fc+"/FinalMap")


##Use a rectangle boundary to clip boundary

##(MAP36) Final Map, final map= clip, input=map35,
##output extent= clipping box shapefile, check the box "use input features"


#Add a labels field to the attribute table for FinalMap to and type in labels
fieldlength = 1050
map37=arcpy.AddField_management (out_fc + "\FinalMap", "Labels", "TEXT", "","", fieldlength)

#Add Labels to the field
fields= ["Value","Labels"]
with arcpy.da.UpdateCursor(map37, fields) as cursor:
    for row in cursor:
        if row[0] == 11:
            row[1] = "Flat or nearly flat plains"
        elif row[0] == 12 :
            row[1] = "Smooth plains with some local relief"
        elif row[0] == 13:
            row[1] = "Irregular plains with low relief"
        elif row[0] == 14:
            row[1] = "Irregular plains with moderate relief"
        elif row[0] == 21:
            row[1] = "Tablelands with moderate relief"
        elif row[0] == 22:
            row[1] = "Tablelands with considerable relief"
        elif row[0] == 23:
            row[1] = "Tablelands with high relief"
        elif row[0] == 24:
            row[1] = "Tablelands with very high relief"
        elif row[0] == 31:
            row[1] = "Plains with hills"
        elif row[0] == 32:
            row[1] = "Plains with high hills"
        elif row[0] == 33:
            row[1] = "Plains with low mountains"
        elif row[0] == 34:
            row[1] = "Plains with high mountains"
        elif row[0] == 41:
            row[1] = "Open very low hills"
        elif row[0] == 42:
            row[1] = "Open low hills"
        elif row[0] == 43:
            row[1] = "Open moderate hills"
        elif row[0] == 44:
            row[1] = "Open high hills"
        elif row[0] == 45:
            row[1] = "Open low mountains"
        elif row[0] == 46:
            row[1] = "Open high mountains"
        elif row[0] == 51:
            row[1] = "Very low hills"
        elif row[0] == 52:
            row[1] = "Low hills"
        elif row[0] == 53:
            row[1]= "Moderate hills"
        elif row[0] == 54:
            row[1] = "High hills"
        elif row[0] == 55:
            row[1] = "Low mountains"
        elif row[0] == 56:
            row[1]= "High mountains"

        cursor.updateRow(row)




#Finalpolys= convert final map to vector (polygons) (raster to polygon)
#arcpy.RasterToPolygon_conversion (map35, outfc )


#change symbology
#arcpy.AddColormap_management(out_fc + "\FinalMap", templateraster )

#create a hillshade raster, drag it to top of stack, change transparency to 60%


