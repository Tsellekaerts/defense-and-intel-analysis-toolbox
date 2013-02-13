
import os, sys, traceback, math, decimal
import arcpy
from arcpy import env
from arcpy import sa

observers = r"C:\Demos\Sprints\2 April 2012\Visibility and Range Template\Maps\default.gdb\templateRLOSObserver"# arcpy.GetParameterAsText(0)
input_surface = r"C:\Demos\Sprints\2 April 2012\Visibility and Range Template\Maps\default.gdb\Jbad_SRTM_USGS_EROS"# arcpy.GetParameterAsText(1)
output_rlos = r"C:\Demos\Sprints\2 April 2012\Visibility and Range Template\Maps\Toolboxes\scratch\scratch.gdb\RLOS"# arcpy.GetParameterAsText(2)
RADIUS2_to_infinity = 'false'# arcpy.GetParameterAsText(3)
envscratchworkspace = r"C:\Demos\Sprints\2 April 2012\Visibility and Range Template\Maps\Toolboxes\scratch\scratch.gdb"

if RADIUS2_to_infinity == 'true':
    arcpy.AddMessage("RLOS to infinity will use horizon for calculation.")
    RADIUS2_to_infinity = True
else:
    arcpy.AddMessage("RLOS will use local RADIUS2 values for calculation.")
    RADIUS2_to_infinity = False


delete_me = []
terrestrial_refractivity_coefficient = 0.13
polygon_simplify = "SIMPLIFY"

def maxVizModifiers(obs):
    maxVizMods = {}
    radius2Max = 0.0
    offsetMax = 0.0
    spotMax = 0.0
    removeSPOT = False  
    rows = arcpy.SearchCursor(obs)
    for row in rows:
        if (row.RADIUS2 > radius2Max): radius2Max = row.RADIUS2
        if (row.OFFSETA > offsetMax): offsetMax = row.OFFSETA
        spot = row.SPOT
        if str(spot) == "None":
            removeSPOT = True
        else:
            if (row.SPOT > spotMax): spotMax = row.SPOT
    del row
    del rows
    maxVizMods = {'SPOT':spotMax,'OFFSETA':offsetMax, 'RADIUS2':radius2Max, 'REMOVE_SPOT':removeSPOT}
    #arcpy.AddMessage("Observer modifier maximums: " + str(maxVizMods))
    return maxVizMods

def zfactor(dataset):
    desc = arcpy.Describe(dataset)
    # if it's not geographic return 1.0
    if desc.spatialReference.type != "Geographic":
        return 1.0
    extent = desc.Extent
    extent_split = [extent.xmin,extent.ymin,extent.xmax,extent.ymax]
       
    top = float(extent_split[3])
    bottom = float(extent_split[1])
    
    #find the mid-latitude of the dataset
    if (top > bottom):
        height = (top - bottom)
        mid = (height/2) + bottom
    elif (top < bottom):  # Unlikely, but just in case
        height = bottom - top
        mid = (height/2) + top
    else: # top == bottom
        mid = top

    # convert degrees to radians
    mid = math.radians(mid)

    # Find length of degree at equator based on spheroid's semi-major axis
    spatial_reference = desc.SpatialReference
    semi_major_axis = spatial_reference.semiMajorAxis # in meters
    equatorial_length_of_degree = ((2.0 * math.pi * float(semi_major_axis))/360.0)

    # function:
    # Z-Factor = 1.0/(111320 * cos(mid-latitude in radians)) 
    decimal.getcontext().prec = 28
    decimal.getcontext().rounding = decimal.ROUND_UP
    a = decimal.Decimal("1.0")
    #b = decimal.Decimal("111320.0") # number of meters in one degree at equator (approximate using WGS84)
    b = decimal.Decimal(str(equatorial_length_of_degree))
    c = decimal.Decimal(str(math.cos(mid)))
    zfactor = a/(b * c)
    zfactor = "%06f" % (zfactor.__abs__())
    return zfactor

try:
    
    # get/set initial environment
    currentOverwriteOutput = env.overwriteOutput
    env.overwriteOutput = True
    # check out spatial analyst license
    arcpy.CheckOutExtension("Spatial")
    installInfo = arcpy.GetInstallInfo("desktop")
    installDirectory = installInfo["InstallDir"]
    GCS_WGS_1984 = os.path.join(installDirectory,r"Coordinate Systems", r"Geographic Coordinate Systems", r"World",r"WGS 1984.prj")  
    
    # get observer's vibility modifier maximums
    obsMaximums = maxVizModifiers(observers)
    removeSPOT = obsMaximums['REMOVE_SPOT']
    if (removeSPOT == True):
        arcpy.AddMessage("Observer SPOT is <NULL>, deleteing field ...")
        arcpy.DeleteField_management(observers,"SPOT")
    
    # Do a Minimum Bounding Geometry (MBG) on the input observers
    observers_mbg = os.path.join(envscratchworkspace,"observers_mbg")#(envscratchworkspace,"observers_mbg")
    delete_me.append(observers_mbg)
    arcpy.AddMessage("Finding observer's minimum bounding envelope ...")
    arcpy.MinimumBoundingGeometry_management(observers,observers_mbg,"RECTANGLE_BY_AREA") # ENVELOPE would be better but would make it ArcInfo-only.
    
    # Now find the center of the (MBG)
    arcpy.AddMessage("Finding center of observers ...")
    mbgCenterPoint = os.path.join(envscratchworkspace,"mbgCenterPoint")#(envscratchworkspace,"mbgCenterPoint")
    mbgExtent = arcpy.Describe(observers_mbg).extent
    mbgSR = arcpy.Describe(observers_mbg).spatialReference
    mbgCenterX = mbgExtent.XMin + (mbgExtent.XMax - mbgExtent.XMin)
    mbgCenterY = mbgExtent.YMin + (mbgExtent.YMax - mbgExtent.YMin)
    arcpy.CreateFeatureclass_management(os.path.dirname(mbgCenterPoint),os.path.basename(mbgCenterPoint),"POINT","#","DISABLED","DISABLED",mbgSR)
    mbgShapeFieldName = arcpy.Describe(mbgCenterPoint).ShapeFieldName
    rows = arcpy.InsertCursor(mbgCenterPoint)
    feat = rows.newRow()
    feat.setValue(mbgShapeFieldName,arcpy.Point(mbgCenterX,mbgCenterY))
    rows.insertRow(feat)
    del rows
    delete_me.append(mbgCenterPoint)
    
    # Get the maximum radius of the observers
    maxRad = obsMaximums['RADIUS2']
    maxOffset = obsMaximums['OFFSETA']
    horizonDistance = 0.0
    z_factor = float(zfactor(observers))
    if RADIUS2_to_infinity == True:
        # if going to infinity what we really need is the distance to the horizon based on height/elevation
        arcpy.AddMessage("Finding horizon distance ...")
        result = arcpy.GetCellValue_management(input_surface, str(mbgCenterX) + " " + str(mbgCenterY))
        centroid_elev = result.getOutput(0)
        R2 = float(centroid_elev) + float(maxOffset)
        R = 6378137.0 # length, in meters, of semimajor axis of WGS_1984 spheroid.
        horizonDistance = math.sqrt(math.pow((R + R2),2) - math.pow(R,2))
        arcpy.AddMessage(str(horizonDistance) + " meters.")
        horizonExtent = str(mbgCenterX - horizonDistance) + " " + str(mbgCenterY - horizonDistance) + " " + str(mbgCenterX + horizonDistance) + " " + str(mbgCenterY + horizonDistance)
        # since we are doing infinity we can drop the RADIUS2 field
        arcpy.AddMessage("Analysis to edge of surface, dropping RADIUS2 field ...")
        arcpy.DeleteField_management(observers,"RADIUS2")
    else:
        pass
    
    # reset center of AZED using Lat/Lon of MBG center point
    # Project point to WGS 84
    arcpy.AddMessage("Recentering Azimuthal Equidistant to centroid ...")
    mbgCenterWGS84 = os.path.join(envscratchworkspace,"mbgCenterWGS84")#(envscratchworkspace,"mbgCenterWGS84")
    arcpy.Project_management(mbgCenterPoint,mbgCenterWGS84,GCS_WGS_1984)
    arcpy.AddXY_management(mbgCenterWGS84)
    pointx = 0.0
    pointy = 0.0
    shapeField = arcpy.Describe(mbgCenterWGS84).ShapeFieldName
    rows = arcpy.SearchCursor(mbgCenterWGS84)
    for row in rows:
        feat = row.getValue(shapeField)
        pnt = feat.getPart()
        pointx = pnt.X
        pointy = pnt.Y
    del row
    del rows
    # write new central meridian and latitude of origin...
    strAZED = 'PROJCS["World_Azimuthal_Equidistant",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Azimuthal_Equidistant"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",' + str(pointx) + '],PARAMETER["Latitude_Of_Origin",' + str(pointy) + '],UNIT["Meter",1.0],AUTHORITY["ESRI",54032]]'
    delete_me.append(mbgCenterWGS84)
    
    # Clip the input surface to the maximum visibilty range and extract it to a 1000 x 1000 raster
    # if going to infinity then clip to horizion extent
    surf_extract = os.path.join(envscratchworkspace,"surf_extract")#(envscratchworkspace,"surf_extract")
    if RADIUS2_to_infinity == True:
        mbgBuffer = os.path.join(envscratchworkspace,"mbgBuffer")#(envscratchworkspace,"mbgBuffer")
        arcpy.Buffer_analysis(observers_mbg,mbgBuffer,horizonDistance)
        delete_me.append(mbgBuffer)
        surfaceSR = arcpy.Describe(input_surface).spatialReference
        mbgBufferPrj = os.path.join(envscratchworkspace,"mbgBufferPrj")#(envscratchworkspace,"mbgBufferPrj")
        arcpy.Project_management(mbgBuffer,mbgBufferPrj,surfaceSR)
        delete_me.append(mbgBufferPrj)
        mbgBufferPrjExtent = arcpy.Describe(mbgBufferPrj).extent
        cellSize = max(float(mbgBufferPrjExtent.width)/1000.0,float(mbgBufferPrjExtent.height)/1000.0)
        env.cellSize = cellSize
        arcpy.AddMessage("Clipping and resampling surface to analysis area with " + str(cellSize) + " meter cell size ...")
        arcpy.Clip_management(input_surface,"#",surf_extract,mbgBufferPrj)
    else:
        # buffer MBG by max RADIUS 2 + 10%
        mbgBuffer = os.path.join(envscratchworkspace,"mbgBuffer")#(envscratchworkspace,"mbgBuffer")
        arcpy.Buffer_analysis(observers_mbg,mbgBuffer,obsMaximums['RADIUS2'])
        delete_me.append(mbgBuffer)
        # project buffer to surface SR
        surfaceSR = arcpy.Describe(input_surface).spatialReference
        mbgBufferPrj = os.path.join(envscratchworkspace,"mbgBufferPrj")
        arcpy.Project_management(mbgBuffer,mbgBufferPrj,surfaceSR)
        delete_me.append(mbgBufferPrj)
        # clip surface to projected buffer
        arcpy.Clip_management(input_surface,"#",surf_extract,mbgBufferPrj)
    delete_me.append(surf_extract)

    # Project surface to the new AZED
    extract_prj = os.path.join(envscratchworkspace,"extract_prj")
    arcpy.AddMessage("Projecting surface ...")
    arcpy.ProjectRaster_management(surf_extract,extract_prj,strAZED)
    delete_me.append(extract_prj)
    
    # Project observers to the new AZED
    obs_prj = os.path.join(envscratchworkspace,"obs_prj")
    arcpy.AddMessage("Projecting observers ...")
    arcpy.Project_management(observers,obs_prj,strAZED)
    delete_me.append(obs_prj)
    
    # Project the MBG buffer to AZED
    obs_buf = os.path.join(envscratchworkspace,"obs_buf")
    #if RADIUS2_to_infinity == True:
    #    arcpy.Buffer_analysis(obs_prj,obs_buf,horizonDistance)
    #else:
    #    arcpy.Project_management(mbgBufferPrj,obs_buf,strAZED)
    arcpy.Project_management(mbgBufferPrj,obs_buf,strAZED)
    delete_me.append(obs_buf)
        
    # Finally ... run Viewshed
    arcpy.AddMessage("Calculating Viewshed ...")
    vshed = os.path.join(envscratchworkspace,"vshed")
    delete_me.append(vshed)
    outVshed = sa.Viewshed(extract_prj,obs_prj,1.0,"CURVED_EARTH",terrestrial_refractivity_coefficient)
    outVshed.save(vshed)
    
    # Raster To Polygon
    arcpy.AddMessage("Converting to polygons ...")
    ras_poly = os.path.join(envscratchworkspace,"ras_poly")
    arcpy.RasterToPolygon_conversion(vshed,ras_poly,polygon_simplify)
    delete_me.append(ras_poly)
    
    # clip output polys to buffer
    arcpy.Clip_analysis(ras_poly,obs_buf,output_rlos)
        
    
    # set output
    arcpy.SetParameter(2,output_rlos)
    
    # cleanup
    arcpy.AddMessage("Removing scratch datasets:")
    for ds in delete_me:
        arcpy.AddMessage(str(ds))
        arcpy.Delete_management(ds)
    # reset overwrite environment to what it was before 
    env.overwriteOutput = currentOverwriteOutput
    
except arcpy.ExecuteError:
    error = True
    # Get the tool error messages 
    msgs = arcpy.GetMessages() 
    arcpy.AddError(msgs) 
    print msgs

except:
    # Get the traceback object
    error = True
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages() + "\n"

    # Return python error messages for use in script tool or Python Window
    arcpy.AddError(pymsg)
    arcpy.AddError(msgs)

    # Print Python error messages for use in Python / Python Window
    print pymsg + "\n"
    print msgs

finally:
    # check in spatial analyst
    arcpy.CheckInExtension("Spatial")
