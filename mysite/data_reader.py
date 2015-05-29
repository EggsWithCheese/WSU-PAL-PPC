'''
Created on Mar 5, 2015

This class reads in data from an excel file, packages it up, and sends it to the model for processing.

@author: cdleong
'''
import xlrd, xlwt #reading and writing, respectively.
from pond_layer import Pond_Layer
from pond import Pond




#Useful notes: http://www.youlikeprogramming.com/2012/03/examples-reading-excel-xls-documents-using-pythons-xlrd/

class DataReader(object):
    '''
    classdocs
    '''

    ##################################
    # class variables
    ##################################
    filename = "template.xlsx" #name of file. Default is "template.xlsx"
    
    #Default sheet names Alternate method: Worksheet indices. 
    pond_data_sheet_index =0
    layer_data_sheet_index = 1        
    pond_data_sheet_name = "pond_data"
    layer_data_sheet_name = "layer_data"

    
    
    #indices for Pond vars in pond_data worksheet
    dayOfYearIndex = 0 #"DOY"
    lakeIDIndex = 1 #"Lake_ID"
    surface_area_index = 2 #"LA.m2"
    gam_index = 3
    kd_index = 4 #index of light attenuation coefficient kd
    noonLightIndex = 5 #"midday.mean.par"
    lengthOfDayIndex = 10 #"LOD" in hours                
    
    #indices for Pond_layer vars
    depth_index = 2 #"z" in meters    
    pmax_index = 3 #"pmax.z"
    area_index = 4 #"kat_div" in meters squared. 
    ikIndex = 5 #"ik_z" light intensity at onset of saturation

    
    #indices for Pond_Layer vars


    def __init__(self, filename, testFlag=0):
        '''
        Constructor
        '''        
        if(2==testFlag): #based off pprinputs_colin.xlsx
            self.filename = "pprinputs_Colin.xlsx"
            self.dayOfYearIndex = 1 #"DOY"
            self.lakeIDIndex = 2 #"Lake_ID"
            self.depth_index = 3 #"z" in meters
            self.surface_area_index = 9 #"LA.m2"
            self.gam_index = 10
            self.pmax_index = 13 #"pmax.z"
            self.kd_index = 14 #index of light attenuation coefficient kd
            self.area_index = 16 #"kat_div" in meters squared. TODO: why is it not even close to LA at z=0?
            self.noonLightIndex = 18 #"midday.mean.par"
            self.ikIndex = 21 #"ik_z" light intensity at onset of saturation
            self.lengthOfDayIndex = 27 #"LOD" in hours

        elif(1==testFlag):#based off inputs_pruned.xlsx
            self.filename = "example.xlsx"
            self.dayOfYearIndex = 0 #"DOY"
            self.lakeIDIndex = 1 #"Lake_ID"
            self.depth_index = 2 #"z" in meters
            self.surface_area_index = 3 #"LA.m2"
            self.gam_index = 4
            self.pmax_index = 5 #"pmax.z"
            self.kd_index = 6 #index of light attenuation coefficient kd
            self.area_index = 7 #"kat_div" in meters squared. TODO: why is it not even close to LA at z=0?
            self.noonLightIndex = 8 #"midday.mean.par"
            self.ikIndex = 9 #"ik_z" light intensity at onset of saturation
            self.lengthOfDayIndex = 10 #"LOD" in hours

        else:
            #use default indices
            self.filename = filename
                       
            

            
                        



    def read(self):
        try:
            book = xlrd.open_workbook(self.filename)
        except:
            raise

        return self.getPondList(book)




    def readFile(self,inputfile):
        #http://stackoverflow.com/questions/10458388/how-do-you-read-excel-files-with-xlrd-on-appengine
        try:
            book =  xlrd.open_workbook(file_contents=inputfile)
        except IOError:
            raise
         
             
        return self.getPondList(book)



    #reads all the pond data from the excel file.
    def getPondList(self,book):
        
        nsheets = book.nsheets
        print "The number of worksheets is", book.nsheets
        
        
        sheet_names = book.sheet_names()
        print "Worksheet name(s):" 
        print sheet_names
        
        pond_data_workSheet = xlrd.book
        layer_data_workSheet= xlrd.book
        
        if(nsheets<2):
            raise IOError("file format incorrect. Number of sheets less than two.")
        
        if(self.pond_data_sheet_name in sheet_names and self.layer_data_sheet_name in sheet_names):
            print "pond_data sheet detected"
            pond_data_workSheet = book.sheet_by_name(self.pond_data_sheet_name)
            print "layer_data sheet detected"
            layer_data_workSheet = book.sheet_by_name(self.layer_data_sheet_name)            
        else:
            print "Standard sheet names not detected. Attempting to read using sheet indices."
            pond_data_workSheet = book.sheet_by_index(self.pond_data_sheet_index)
            layer_data_workSheet = book.sheet_by_index(self.layer_data_sheet_index)
        

            
        pond_data_workSheet_num_rows = pond_data_workSheet.nrows-1
        print "the number of rows in sheet " + pond_data_workSheet.name +  " is " + str(pond_data_workSheet_num_rows)
        
        layer_data_workSheet_num_rows = layer_data_workSheet.nrows-1
        print "the number of rows in sheet " + layer_data_workSheet.name + " is " + str(layer_data_workSheet_num_rows)
        
        curr_row =0
        columnnames = pond_data_workSheet.row(curr_row)
        print "the column names in sheet \"" + pond_data_workSheet.name +  "\" are "
        print columnnames

        curr_row =0
        columnnames = layer_data_workSheet.row(curr_row)
        print "the column names in sheet \"" + layer_data_workSheet.name +  "\" are "
        print columnnames        


        
        
        #################################################
        #make all the objects
        #################################################
        pondList = [] #list of pond objects. The same water body on a different day counts as a separate "Pond"


        ################################################
        #Make Pond objects
        ################################################
#         #for each row
#         curr_row = 1 #start at 1. row 0 is column headings
#         while curr_row<num_rows:
#             row = workSheet.row(curr_row)
#             if (1==curr_row):
#                 print "row #", curr_row, " is ", row
# 
#             #extract relevant values from row
#             row_doy_value = row[dayOfYearIndex].value
#             row_lakeID_value = row[lakeIDIndex].value
#             row_depth_value = row[depth_index].value
#             row_surface_area_value = row[surface_area_index].value
#             row_gam_value = row[gam_index].value
#             row_pmax_value = row[pmax_index].value
#             row_kd_value = row[kd_index].value
#             row_area_value = row[area_index].value
#             row_noonlight_value = row[noonLightIndex].value
#             row_ik_value = row[ikIndex].value
#             row_lod_value = row[lengthOfDayIndex].value
# 
# 
#             #totalPhos value arbitrarily picked
#             totalphos_value = 500.0
# 
# 
#             #create Pond_Layer object using values specific to that layer/row
#             layer = Pond_Layer()
#             layer.set_depth(row_depth_value)
#             layer.set_ik(row_ik_value)
#             layer.set_pmax(row_pmax_value)
#             layer.set_area(row_area_value)
# 
#             #Do we need to make a pond object?
#             pond = next((i for i in pondList if (i.getLakeID()== row_lakeID_value and i.getDayOfYear()==row_doy_value)),None) #source: http://stackoverflow.com/questions/7125467/find-object-in-list-that-has-attribute-equal-to-some-value-that-meets-any-condi
# 
#             if pond is None: #not in list. Must create Pond object
#                 print "creating pond with lake ID = ", row_lakeID_value, " , and DOY = ", row_doy_value
#                 pond = Pond()
#                 pond.setDayOfYear(row_doy_value)
#                 pond.setLakeID(row_lakeID_value)
#                 pond.setShapeFactor(row_gam_value)
#                 pond.setBackgroundLightAttenuation(row_kd_value)
#                 pond.setNoonSurfaceLight(row_noonlight_value)
#                 pond.setDayLength(row_lod_value)
#                 pond.setPondLayerList([]) #set to empty list I hope
#                 #why do I need to do that
#                 #that makes no darn sense
#                 pond.setSufaceAreaAtDepthZero(row_surface_area_value)
#                 pond.setTotalPhos(totalphos_value)
# 
# 
# 
#     #             print "appending layer 1"
#                 pond.appendPondLayerIfPhotic(layer)
# 
#     #             print "appending pond"
#                 pondList.append(pond)
# 
#             else: #Pond exists. just append the PondLayer
#                 pond.appendPondLayerIfPhotic(layer)
# 
#             print "curr_row = ", curr_row, " size of pond list is: ", len(pondList)
#             curr_row+=1
            #end of while loop!

 
        return pondList

    def write(self, filename="output.xls"):

        #Create a new workbook object
        workbook = xlwt.Workbook()

        #Add a sheet
        worksheet = workbook.add_sheet('Statistics')

        #Add some values
        for x in range(0, 10):
            for y in range(0,10):
                worksheet.write(x,y,x*y)

        workbook.save(filename)

'''
let us test things
'''
def main():
    print "hello world"
#     filename = "static/template.xlsx"
    filename = "static/"+DataReader.filename

    reader = DataReader(filename)
    pondList = reader.read()
#     pond = pondList[0]
#     bppr0=pond.calculateDailyWholeLakeBenthicPrimaryProductionPerMeterSquared()

#     bpproneline = reader.read()[0].calculateDailyWholeLakeBenthicPrimaryProductionPerMeterSquared(0.25)

    for p in pondList:
        bppr = p.calculateDailyWholeLakeBenthicPrimaryProductionPerMeterSquared()
        pid = p.getLakeID()
        print "Daily Whole Lake Primary Production Per Meter Squared For lake ID " + pid + " is " + str(bppr)
        









if __name__ == "__main__":
    main()