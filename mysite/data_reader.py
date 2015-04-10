'''
Created on Mar 5, 2015

@author: cdleong
'''
import xlrd, xlwt #reading and writing, respectively. 
from pond_layer import Pond_Layer
from pond import Pond
import numpy as np


#Useful notes: http://www.youlikeprogramming.com/2012/03/examples-reading-excel-xls-documents-using-pythons-xlrd/

class DataReader(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        
'''
let us test things
'''
def main(): 
    print "hello world"
    book = xlrd.open_workbook("pprinputs_Colin.xlsx")
    print "The number of worksheets is", book.nsheets
    print "Worksheet name(s):", book.sheet_names()
    
    
    #workSheet = book.sheet_by_index(0)
    workSheet = book.sheet_by_name('pprinputs')

    
    num_rows = workSheet.nrows-1
    
    print "the number of rows is", num_rows
    
    curr_row =0
    
    columnnames = workSheet.row(curr_row)
    
    print columnnames
    
    #
    
    
    
    
    #I successfully printed a row. I have discovered how to read data from excel spreadsheets.
    #success.
    
    
    ##############################################
    #all the data indices
    ##############################################
    #based off pprinputs_colin.xlsx
    dayOfYearIndex = 1 #"DOY" 
    lakeIDIndex = 2 #"Lake_ID"
    depth_index = 3 #"z" in meters
    surface_area_index = 9 #"LA.m2"
    gam_index = 10
    pmax_index = 13 #"pmax.z"
    kd_index = 14 #index of light attenuation coefficient kd
    area_index = 16 #"kat_div" in meters squared. TODO: why is it not even close to LA at z=0?      
    noonLightIndex = 18 #"midday.mean.par"      
    ikIndex = 21 #"ik_z" light intensity at onset of saturation     
    lengthOfDayIndex = 27 #"LOD" in hours   
 



    
    
    
    #################################################
    #make all the objects
    #################################################
    pondList = [] #list of pond objects. The same water body on a different day counts as a separate "Pond"
    
    #for each row
    curr_row = 1 #start at 1. row 0 is column headings
    while curr_row<num_rows:
        row = workSheet.row(curr_row)
        if (1==curr_row):
            print "row #", curr_row, " is ", row
        
        #extract relevant values from row
        row_doy_value = row[dayOfYearIndex].value
        row_lakeID_value = row[lakeIDIndex].value
        row_depth_value = row[depth_index].value
        row_surface_area_value = row[surface_area_index].value
        row_gam_value = row[gam_index].value
        row_pmax_value = row[pmax_index].value
        row_kd_value = row[kd_index].value
        row_area_value = row[area_index].value
        row_noonlight_value = row[noonLightIndex].value
        row_ik_value = row[ikIndex].value
        row_lod_value = row[lengthOfDayIndex].value
        
        
        #totalPhos value arbitrarily picked
        totalphos_value = 500.0
        

        #create Pond_Layer object using values specific to that layer/row
        layer = Pond_Layer() 
        layer.set_depth(row_depth_value)
        layer.set_ik(row_ik_value)
        layer.set_pmax(row_pmax_value)
        layer.set_area(row_area_value)
        
        #Do we need to make a pond object?         
        pond = next((i for i in pondList if (i.getLakeID()== row_lakeID_value and i.getDayOfYear()==row_doy_value)),None) #source: http://stackoverflow.com/questions/7125467/find-object-in-list-that-has-attribute-equal-to-some-value-that-meets-any-condi
        
        if pond is None: #not in list. Must create Pond object
            print "creating pond with lake ID = ", row_lakeID_value, " , and DOY = ", row_doy_value
            pond = Pond()
            pond.setDayOfYear(row_doy_value)
            pond.setLakeID(row_lakeID_value)
            pond.setShapeFactor(row_gam_value)
            pond.setBackgroundLightAttenuation(row_kd_value)
            pond.setNoonSurfaceLight(row_noonlight_value)
            pond.setDayLength(row_lod_value)
            pond.setPondLayerList([]) #set to empty list I hope
            #why do I need to do that
            #that makes no darn sense                        
            pond.setSufaceAreaAtDepthZero(row_surface_area_value)
            pond.setTotalPhos(totalphos_value)

            
            
#             print "appending layer 1"
            pond.appendPondLayerIfPhotic(layer)
            
#             print "appending pond"
            pondList.append(pond)
            
        else: #Pond exists. just append the PondLayer
            print "appending layer to pond with lake ID = ", pond.getLakeID(), " , and DOY = ", pond.getDayOfYear()
            print "length of pondLayerList is now ", len(pond.pondLayerList)
            pond.appendPondLayerIfPhotic(layer)
            print "length of pondLayerList is now ", len(pond.pondLayerList)
            
                
        

        
        print "curr_row = ", curr_row, " size of pond list is: ", len(pondList)
        curr_row+=1    
        #end of while loop!
    
    print "**************************************************************************"
    print "done with loop, now we have a bunch of ponds. Let's do a bit of checking. "
    print "**************************************************************************"
    
    print "***********************************************************************************"
    for pond in pondList:
        pppr = pond.calculateDailyWholeLakePelagicPrimaryProduction(0.25)
#         print "lake ID: ", pond.getLakeID(), ", DOY: ", pond.getDayOfYear(), ", surface area (ha): ", pond.getSufaceAreaAtDepthZero()/10000, ", total littoral area: ", pond.calculateTotalLittoralArea(), ",\n whole lake PPPR (mg C *day^-1): ", pppr
#         bppr = pond.calculateDailyWholeLakeBenthicPrimaryProductionPerMeterSquared(0.25) #use quarter-hours
#         bpprPerHour = bppr/pond.getDayLength()
        
#         print "lake ID: ", pond.getLakeID(), ", DOY: ", pond.getDayOfYear(), ", number of Layers: ", len(pond.pondLayerList), ", surface area (ha): ", pond.getSufaceAreaAtDepthZero()/10000, ", total littoral area: ", pond.calculateTotalLittoralArea(), ",\n whole lake BPPR (mg C *m^-2*day^-1): ", bppr, ", BPPR (mg C * m^-2*hour^-1)", bpprPerHour
        print "***********************************************************************************"
        


    
    

        
            
            
        
        
        
        
        
        
        
        
        
    
    
    
    
        
        
        
        

        
    
    
    
    
    
  
    
    
    
     
    
    
    
    
if __name__ == "__main__":
    main()