# -*- coding: utf-8 -*-
"""
Created on Thu Jun 05 09:38:17 2014

@author: cdleong
"""

import math as mat
import numpy as np
from mysite.pond_shape import PondShape
from mysite.benthic_photosynthesis_measurement import BenthicPhotoSynthesisMeasurement
from mysite.bathymetric_pond_shape import BathymetricPondShape
from scipy.interpolate import interp1d
from scipy import interpolate








class Pond(object):

    ###################################
    # CONSTANTS
    ###################################
    MINIMUM_VALID_DAY = 0
    MAXIMUM_VALID_DAY = 366
    
    MINIMUM_LENGTH_OF_DAY = 0.0  # north of the arctic circle and south of the antarctic one, this is possible during winter.
    MAXIMUM_LENGTH_OF_DAY = 24.0003  # north of the arctic circle and south of the antarctic one, this is possible during summer, if there's a leap second
    
    MINIMUM_NOON_SURFACE_LIGHT = 0.0
    MAXIMUM_NOON_SURFACE_LIGHT = 1000000.0  # normally it's in the range of ~1000-2000. A 1000x increase, I'm pretty sure, would sterilize the lake
    
    
    MINIMUM_LIGHT_ATTENUATION_COEFFICIENT = 0.0
    MAXIMUM_LIGHT_ATTENUATION_COEFFICIENT = float("inf")  # no upper limit
    
    PHOTIC_ZONE_LIGHT_PENETRATION_LEVEL_LOWER_BOUND = 0.01 #1% 
    


    
    ###################################
    # VARIABLES
    ###################################    
    
    # identifying variables, aka Primary Key
    lake_ID = -1  # invalid lake ID I'm assuming    
    day_of_year = 0  # day of year 0-366    
 
 
    # General pond information. Light/photosynthesis
    length_of_day = 15  # hours of sunlight
    noon_surface_light = 1500  # micromol*m^(-2)*s^(-1 ) (aka microEinsteins?)
    light_attenuation_coefficient = 0.05  # aka "kd"
    
    # shape
    pond_shape_object = PondShape()
    
    # benthic photosynthesis data list
    benthic_photosynthesis_measurements = []
    
    # phytoplankton photosynthesis data list #TODO: everything to do with this
    phytoplankton_photosynthesis_measurements = []
    
    # default intervals for calculatations 
    time_interval = 0.25


    
    
    ############################
    # CONSTRUCTOR
    ###########################
    def __init__(self,
                 lake_ID="",
                 day_of_year=0,
                 length_of_day=0.0,
                 noon_surface_light=0.0,
                 light_attenuation_coefficient=0.0,
                 pond_shape_object=PondShape(),
                 benthic_photosynthesis_measurements=[],
                 phytoplankton_photosynthesis_measurements=[],
                 time_interval=0.25):
        '''
        CONSTRUCTOR
        @param lake_ID:
        @param day_of_year:
        @param length_of_day:
        @param noon_surface_light:
        @param light_attenuation_coefficient:
        @param pond_shape_object: a PondShape object      
        @param benthic_photosynthesis_measurements: a list of BenthicPhotoSynthesisMeasurements
        @param phytoplankton_photosynthesis_measurements:  a list of PhyttoplanktonPhotoSynthesisMeasurements
        '''
        self.set_lake_id(lake_ID)
        self.set_day_of_year(day_of_year)
        self.length_of_day = length_of_day
        self.noon_surface_light = noon_surface_light
        self.light_attenuation_coefficient = light_attenuation_coefficient
        self.set_pond_shape(pond_shape_object)
        self.set_benthic_photosynthesis_measurements(benthic_photosynthesis_measurements)
        self.set_phytoplankton_photosynthesis_measurements(phytoplankton_photosynthesis_measurements)
        self.set_time_interval(time_interval)

    def get_time_interval(self):
        return self.__time_interval


    def set_time_interval(self, value):
        self.__time_interval = value


    def del_time_interval(self):
        del self.__time_interval








    ###################
    # VALIDATORS
    ###################
    
    def validate_numerical_value(self, value, max_value, min_value):
        '''
        Generic numerical validator. 
        Checks if value is >max_value or <min_value.
        If it's outside the valid range it'll be set to the closest valid value.
        @param value: numerical value of some sort to be checked.
        @param max_value: numerical value. Max valid value.
        @param min_value: numerical value. Min valid value.
        @return: a valid value in the range (min_value,max_value), inclusive 
        @rtype: numerical value  
        '''
        validated_value = 0
        if(value < min_value):
            validated_value = min_value
        elif(value > max_value):
            validated_value = max_value
        else: 
            validated_value = value
        return validated_value        
    
    def validate_day_of_year(self, day_of_year=0):
        '''
        
        @param day_of_year: the day of year the measurement was made.
        @return: a valid value in the range (Pond.MINIMUM_VALID_DAY,Pond.MAXIMUM_VALID_DAY), inclusive 
        @rtype: int
        '''        
        return self.validate_numerical_value(day_of_year, Pond.MAXIMUM_VALID_DAY, Pond.MINIMUM_VALID_DAY)
            
    def validate_length_of_day(self, length_of_day=0.0):
        '''
        
        @param length_of_day:
        @return: a valid value in the range (Pond.MINIMUM_LENGTH_OF_DAY,Pond.MAXIMUM_LENGTH_OF_DAY), inclusive 
        @rtype:  float
        '''
        return self.validate_numerical_value(length_of_day, Pond.MAXIMUM_LENGTH_OF_DAY, Pond.MINIMUM_LENGTH_OF_DAY)     
    
    def validate_proportional_value(self, proportional_value):
        '''
        @param proportional_value:
        @return: a value in the range (0.0, 1.0) inclusive
        @rtype: float 
        '''
        validated_proportional_value = self.validate_numerical_value(proportional_value, 1.0, 0.0)
        return validated_proportional_value
    
    def validate_depth(self, depth=0.0):
        '''
        @param depth:
        @return: 
        @rtype: float
        '''
        pond_shape_object = self.get_pond_shape()
        validated_depth = pond_shape_object.validate_depth(depth)
        return validated_depth
    
    def validate_noon_surface_light(self, noon_surface_light=0.0):
        '''
        @param noon_surface_light:
        @return: 
        @rtype: float 
        '''
        validated_noon_surface_light = self.validate_numerical_value(noon_surface_light, Pond.MAXIMUM_NOON_SURFACE_LIGHT, Pond.MINIMUM_NOON_SURFACE_LIGHT)
        return validated_noon_surface_light
    
    def validate_light_attenuation_coefficient(self, light_attenuation_coefficient):
        validated_light_attenuation_coefficient = self.validate_numerical_value(light_attenuation_coefficient, Pond.MAXIMUM_LIGHT_ATTENUATION_COEFFICIENT, Pond.MINIMUM_LIGHT_ATTENUATION_COEFFICIENT)
        return validated_light_attenuation_coefficient
    
    def validate_types_of_all_items_in_list(self, items=[], desired_type=object):
        '''
        @param items:
        @param desired_type:

        '''
        all_valid = False
        if(all(isinstance(item, desired_type) for item in items)):            
            all_valid = True
        else: 
            all_valid = False
        return all_valid









    #######################
    # GETTERS
    #######################
    def get_lake_id(self):
        '''
        Get Lake ID
        Getter method.
        @return: the ID of the lake.
        @rtype: string
        '''
        return self.__lake_ID


    def get_day_of_year(self):
        '''
        Get Day of Year
        Getter method.
        @return: the day of on which measurements occurred.
        @rtype: int
        '''
        return self.__day_of_year


    def get_length_of_day(self):
        '''
        Get Length Of Day
        Getter method
        @return: the length of day, in hours, on the day of measurements.
        @rtype: float
        '''
        return self.__length_of_day


    def get_noon_surface_light(self):
        '''
        Get Noon Surface Light
        @return: The surface light intensite at solar noon, in micromoles per square meter per second(μmol*m^-2*s^-1)
        @rtype: float
        '''
        return self.__noon_surface_light


    def get_light_attenuation_coefficient(self):
        '''
        Get Light Attenuation Coefficient. 
        AKA background light attenuation, kd.
        @return:light attenuation coefficient.  
        @rtype: float
        '''
        return self.__light_attenuation_coefficient

    def get_pond_shape(self):
        '''
        Get Pond Shape
        @return: a PondShape object, holding all the information describing the shape of the lake.
        @rtype: PondShape
        '''
        return self.pond_shape_object


    def get_benthic_photosynthesis_measurements(self):
        '''
        Get Benthic Photosynthesis Measurements
        @return: the list containing all the Benthic Photosynthesis Measurement objects, that hold the information regarding benthic photosynthesis.
        @rtype: list containing BenthicPhotoSynthesisMeasurement objects
        '''
        return self.__benthic_photosynthesis_measurements


    def get_phytoplankton_photosynthesis_measurements(self):
        '''
        Get Phytoplankton Photosynthesis Measurements
        @return: the list containing all the Phytoplankton Photosynthesis Measurement objects, that hold the information regarding benthic photosynthesis.
        @rtype: list containing PhytoplanktonPhotoSynthesisMeasurement objects        
        '''
        return self.__phytoplankton_photosynthesis_measurements
    



    

    
    def get_max_depth(self):
        return self.get_pond_shape().get_max_depth()
    
    #######################
    # SETTERS
    #######################

    def set_lake_id(self, lake_id):
        '''
        Setter method
        '''
        self.__lake_ID = lake_id


    def set_day_of_year(self, day_of_year):
        '''
        Setter method
        Validates the value        
        '''        
        validated_day_of_year = self.validate_day_of_year(day_of_year)
        self.__day_of_year = validated_day_of_year


    def set_length_of_day(self, length_of_day):
        '''
        Setter method
        Validates the length_of_day        
        '''     
        validated_length_of_day = self.validate_length_of_day(length_of_day)
        self.__length_of_day = validated_length_of_day


    def set_noon_surface_light(self, noon_surface_light):
        '''
        Setter method
        Validates the value        
        '''   
        validated_light = self.validate_noon_surface_light(noon_surface_light)
        self.__noon_surface_light = validated_light


    def set_light_attenuation_coefficient(self, light_attenuation_coefficient):
        '''
        Setter method
        Validates the value        
        '''           
        validated_light_attenuation_coefficient = self.validate_light_attenuation_coefficient(light_attenuation_coefficient)
        self.__light_attenuation_coefficient = validated_light_attenuation_coefficient

        
    def set_pond_shape(self, pond_shape_object):
        '''
        Setter method
        Validates the value        
        '''           
        if(isinstance(pond_shape_object, PondShape)):
            print "setting pond shape."
            self.pond_shape_object = pond_shape_object
        else:
            raise Exception("cannot set pond shape. Invalid type")
        

    def set_benthic_photosynthesis_measurements(self, values=[]):
        '''
        Setter method
        Validates the value        
        '''           
        all_valid = self.validate_types_of_all_items_in_list(values, BenthicPhotoSynthesisMeasurement)
        if(all_valid):
            self.__benthic_photosynthesis_measurements = values
        else:
            raise Exception("ERROR: all values in benthic_photosynthesis_measurements must be of type BenthicPhotoSynthesisMeasurement")


    def set_phytoplankton_photosynthesis_measurements(self, value):
        # TODO: Type-checking
        self.__phytoplankton_photosynthesis_measurements = value
        






    #############################
    # WEIRD AUTOGENERATED THINGS
    #############################        

    def del_lake_id(self):
        del self.__lake_ID


    def del_day_of_year(self):
        del self.__day_of_year


    def del_length_of_day(self):
        del self.__length_of_day


    def del_noon_surface_light(self):
        del self.__noon_surface_light


    def del_light_attenuation_coefficient(self):
        del self.__light_attenuation_coefficient


    def del_benthic_photosynthesis_measurements(self):
        del self.__benthic_photosynthesis_measurements


    def del_phytoplankton_photosynthesis_measurements(self):
        del self.__phytoplankton_photosynthesis_measurements







    lake_ID = property(get_lake_id, set_lake_id, del_lake_id, "lake_ID's docstring")
    day_of_year = property(get_day_of_year, set_day_of_year, del_day_of_year, "day_of_year's docstring")
    length_of_day = property(get_length_of_day, set_length_of_day, del_length_of_day, "length_of_day's docstring")
    noon_surface_light = property(get_noon_surface_light, set_noon_surface_light, del_noon_surface_light, "noon_surface_light's docstring")
    light_attenuation_coefficient = property(get_light_attenuation_coefficient, set_light_attenuation_coefficient, del_light_attenuation_coefficient, "light_attenuation_coefficient's docstring")
    benthic_photosynthesis_measurements = property(get_benthic_photosynthesis_measurements, set_benthic_photosynthesis_measurements, del_benthic_photosynthesis_measurements, "benthic_photosynthesis_measurements's docstring")
    phytoplankton_photosynthesis_measurements = property(get_phytoplankton_photosynthesis_measurements, set_phytoplankton_photosynthesis_measurements, del_phytoplankton_photosynthesis_measurements, "phytoplankton_photosynthesis_measurements's docstring")

                     
       



    ########################################
    # Appenders/mutators
    ########################################
    def add_benthic_measurement(self, measurement=BenthicPhotoSynthesisMeasurement):
        if(isinstance(measurement, BenthicPhotoSynthesisMeasurement)):
            self.benthic_photosynthesis_measurements.append(measurement)
        else:
            raise Exception("ERROR: cannot add measurement to benthic measurements list - measurement must be of type BenthicPhotoSynthesisMeasurement")

    def add_benthic_measurement_if_photic(self, measurement):
        z1Percent = self.calculate_depth_of_specific_light_percentage(self.PHOTIC_ZONE_LIGHT_PENETRATION_LEVEL_LOWER_BOUND)
        if(measurement.get_depth()<z1Percent):
            self.add_benthic_measurement(measurement)
        else: 
            print "measurement not within photic zone"

        
        
    def remove_benthic_measurement(self, measurement=BenthicPhotoSynthesisMeasurement):
        self.benthic_photosynthesis_measurements.remove(measurement)
        
    def update_shape(self, other_pond_shape):
        our_shape = self.get_pond_shape()
        if(isinstance(other_pond_shape, BathymetricPondShape)):
            our_shape.update_shape(other_pond_shape)
            self.pond_shape_object = our_shape


    ########################################
    # SCIENCE FUNCTIONS
    ########################################
    def check_if_depth_in_photic_zone(self, depth):
        in_zone = True
        photic_zone_lower_bound = self.calculate_photic_zone_lower_bound() 
        if(depth<0 or depth>photic_zone_lower_bound):
            in_zone = False
        else: 
            in_zone = True
        return in_zone
        
    def calculate_photic_zone_lower_bound(self):
        lower_bound = self.calculate_depth_of_specific_light_percentage(self.PHOTIC_ZONE_LIGHT_PENETRATION_LEVEL_LOWER_BOUND)
        return lower_bound
        
        

    
        
    def calculate_depth_of_specific_light_percentage(self, desired_light_proportion=1.0):
        '''
        Calculate Depth Of Specific Light Proportion
        
        Calculates the depth of, say, 1% light.
        Uses: light attenuation coefficient kd. 
        This is how "optical depth" works.         
        
        Given a proportion, say 0.01 for 1%, 
        calculates the depth of the pond at which that much light will reach.
        
        Equation on which this is based: Iz/I0=e^-kd*z
        Given a desired proportion for Iz/I0, and solved for z, this simplifies to 
        z= kd/ln(desired proportion)
        
         
         
        @param desired_light_proportion:a float value from 0 to 1.0 
        @return: the depth, in meters, where that proportion of light penetrates.
        @rtype: float         
        '''         
        validated_desired_light_proportion = self.validate_proportional_value(desired_light_proportion)
        depthOfSpecifiedLightProportion = 0.0  # the surface of the pond makes a good default
        backgroundLightAttenuation = self.get_light_attenuation_coefficient()
        
         

 
        if(validated_desired_light_proportion < 1.0 and validated_desired_light_proportion > 0.0):         
            naturalLogOfProportion = mat.log(validated_desired_light_proportion)
             
            depthOfSpecifiedLightProportion = naturalLogOfProportion / -backgroundLightAttenuation  # TODO: check if zero.
         
         
             
             
        return depthOfSpecifiedLightProportion 
    
    def calculate_light_proportion_at_depth(self, depth=0.0):
        '''
        Calculate Light Proportion at Depth
                
        The inverse operation of "Calculate Depth Of Specific Light Proportion". Given the depth, calculates what proportion of light
        will be visible at that depth.
        
        Given a depth, say "10" for 10 meters, calculates the proportion of light (Iz/I0) that will reach that depth 
        
        Equation on which this is based: Iz/I0=e^-kd*z        
        
        If you want Iz, just do Iz*I0 again. #TODO: just light at depth z
        
        @param depth: depth in meters. 
        @return: proportion of light at depth z as a number in the range (0.0, 1.0), inclusive. 
        @rtype:  float
        '''       
        validated_depth = self.validate_depth(depth)
        light_attenuation_coefficient = self.get_light_attenuation_coefficient()
        multiplied = light_attenuation_coefficient * validated_depth
        light_proportion_at_depth = mat.exp(-multiplied)
        return light_proportion_at_depth
    

    def calculate_benthic_primary_productivity(self, light_at_time_and_depth, benthic_pmax_z, benthic_ik_z):
        '''
        Equation for productivity that doesn't include photoinhibition, etc. 
        TODO: Source of this equation? Doesn't match the one from Wikipedia. 
        '''
        bpprzt = benthic_pmax_z * np.tanh(light_at_time_and_depth / benthic_ik_z)
        return bpprzt
    
    
    def calculateDailyWholeLakeBenthicPrimaryProductionPerMeterSquared(self):        
        '''
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        Everything else in this entire project works to make this method work.
        @return: Benthic Primary Production, mg C per meter squared, per day.
        @rtype: float 
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        '''
        time_interval = self.get_time_interval()
        noonlight = self.get_noon_surface_light()
        lod = self.get_length_of_day()
        kd = self.get_light_attenuation_coefficient()
        total_littoral_area = self.calculate_total_littoral_area()
 
 
        
        depth_interval =0.1 #TODO: undo this
        benthic_primary_production_answer = 0.0  # mg C per day
        current_depth = 0.0
        shape_object = self.get_pond_shape()        
#         # for each current_depth interval
#         for depth, area in shape_object.water_surface_areas.items():
#             current_depth = depth
#             bpprz = 0.0  # mg C* m^-2 *day
#   
#             # for every time interval
#              
#             ik_z = self.get_benthic_ik_at_depth(current_depth)
#             benthic_pmax_z = self.get_benthic_pmax_at_depth(current_depth)  # units?
#             area_z = area
#             f_area = area_z/total_littoral_area
#                  
#             t = 0.0  # start of day
#             while t < lod:
#   
#                 light_t = noonlight * np.sin(np.pi * t / lod)  # light at current_depth current_depth, time t
#                 izt = light_t * np.exp(-kd * current_depth)
#                 bpprzt = benthic_pmax_z * np.tanh(izt / ik_z)
#                 bpprz += bpprzt
#   
#                 t += time_interval
#             bpprz = bpprz / (1 / time_interval)  # account for the fractional time interval. e.g. dividing by 1/0.25 is equiv to dividing by 4
#             interval_bppr_fraction = bpprz * f_area  # normalizing
#  
#  
#   
#             benthic_primary_production_answer += interval_bppr_fraction
#             current_depth += depth_interval 
            
        current_depth_interval = 0.0
        previous_depth = 0.0
        measurement_depths = []
        runningTotal=0
        for measurement in self.benthic_photosynthesis_measurements:
            
            measurement_depth = measurement.get_depth()
            previous_depth = current_depth
            current_depth = measurement_depth
            
            ik_z = measurement.get_ik()
            benthic_pmax_z = measurement.get_pmax()                     
             
            current_depth_interval = current_depth-previous_depth
            area = self.get_pond_shape().get_sediment_surface_area_at_depth(current_depth, current_depth_interval)
            runningTotal+=area            
            measurement_depths.append(measurement_depth)

        print "total littoral area from sum-of-chunks method is: ", runningTotal
        current_depth_interval = 0.0
        previous_depth = 0.0
        current_depth = 0.0
        f_area_total = 0.0 #should end up adding to 1.0
        sorted_measurement_depths = sorted(measurement_depths)
        for measurement_depth in sorted_measurement_depths:
                        
            previous_depth = current_depth
            current_depth = measurement_depth
             
            current_depth_interval = current_depth-previous_depth
            area = self.get_pond_shape().get_sediment_surface_area_at_depth(current_depth, current_depth_interval)
            bpprz = 0.0  # mg C* m^-2 *day
  
            # for every time interval
             
#             ik_z = self.get_benthic_ik_at_depth(current_depth)
#             benthic_pmax_z = self.get_benthic_pmax_at_depth(current_depth)  # units?
            measurement = next((i for i in self.benthic_photosynthesis_measurements if (i.get_depth()==measurement_depth)),None)
            
                
            ik_z = measurement.get_ik()
            benthic_pmax_z = measurement.get_pmax()          
#             print "ik is ", ik_z, " and pmax is ", benthic_pmax_z  

             
#             f_area = area/total_littoral_area
#             total_littoral_area = self.get_pond_shape().get_water_surface_area_at_depth(0)

            #calculate fractional area using the area at highest depth - area at lowest depth method.
#             f_area = shape_object.get_fractional_sediment_area_at_depth(current_depth, total_littoral_area, current_depth_interval) #TODO: debug this method. It doesn't work right.

            #calculate fractional area with a running total of chunk areas
            total_littoral_area=runningTotal
            f_area = area/total_littoral_area
            f_area_total+=f_area
            
            
            #calculate area and fractional area using total_littoral_area = "sum up water surface area at every depth greater than 1% light" method. 
#             area = shape_object.get_water_surface_area_at_depth(current_depth)
#             total_littoral_area = 0.0
#             shape_dictionary = self.pond_shape_object.water_surface_areas
#             depth_keys = shape_dictionary.keys()
#             for item in depth_keys:
#                 depth = item
#                 this_area = shape_dictionary[depth]
#                 if(depth< self.calculate_photic_zone_lower_bound()):
#                     total_littoral_area+=this_area
#             f_area = area/total_littoral_area

            
                 
            t = 0.0  # start of day
            while t < lod:
  
                izt = self.calculate_light_at_depth_and_time(current_depth, t)
                bpprzt = self.calculate_benthic_primary_productivity(izt, benthic_pmax_z, ik_z)
                bpprz += bpprzt
  
                t += time_interval
            bpprz = bpprz / (1 / time_interval)  # account for the fractional time interval. e.g. dividing by 1/0.25 is equiv to dividing by 4
            interval_bppr_fraction = bpprz * f_area  # normalizing
            
#             if(f_area>0):
#                 print "for depth interval ",current_depth,"-",previous_depth,", f_area is", f_area, ", with total littoral area of ", total_littoral_area, ". Resulting bppr: ", interval_bppr_fraction
#                 print "f_area total adds to ", f_area_total
                    
                
            benthic_primary_production_answer += interval_bppr_fraction             
  
 
        return benthic_primary_production_answer
    
    

    def validate_time(self, time):
        validated_time =time
        length_of_day = self.get_length_of_day()
        if(time>length_of_day):
            validated_time =length_of_day
        elif(time<0.0):
            validated_time = 0.0
         
            
        return validated_time
    
    
    def calculate_light_at_depth_and_time(self, depth, time):
        
        validated_depth = self.validate_depth(depth)
        validated_time = self.validate_time(time)
        noonlight = self.get_noon_surface_light()
        length_of_day = self.get_length_of_day()
        surface_light_at_t = noonlight * np.sin(np.pi * validated_time / length_of_day)
        light_attenuation_coefficient = self.get_light_attenuation_coefficient()
        light_at_z_and_t = surface_light_at_t* np.exp(-light_attenuation_coefficient * validated_depth)
        return light_at_z_and_t
        

    
    def calculate_total_littoral_area(self):
        '''
        @return:
        @rtype:  
        '''
        z1percent = self.calculate_photic_zone_lower_bound()        
        shape_of_pond = self.get_pond_shape()
        
        littoral_area = shape_of_pond.get_sediment_area_above_depth(z1percent, z1percent)
        return littoral_area    
    
    def get_benthic_pmax_at_depth(self, depth=0.0):
        '''
        @return:
        @rtype:  
        '''    
        #if depth is lower than the depth of 1% light, pmax approaches zero.
        if(self.check_if_depth_in_photic_zone(depth)==False):
            return 0
        
        
        validated_depth = self.validate_depth(depth)            
        pmax_values_list = []
        depths_list = []
        for measurement_value in self.get_benthic_photosynthesis_measurements():
            pmax_value = measurement_value.get_pmax()
            depth_value = measurement_value.get_depth()
            pmax_values_list.append(pmax_value)
            depths_list.append(depth_value)
        bpmax_at_depth = self.interpolate_values_at_depth(validated_depth, depths_list, pmax_values_list)
        return bpmax_at_depth
    
    def get_benthic_ik_at_depth(self, depth=0.0):
        '''
        @return: 
        @rtype: 
        '''
        validated_depth = self.validate_depth(depth)
        

        values_list = []
        depths_list = []
        for measurement_value in self.get_benthic_photosynthesis_measurements():
            ik_value = measurement_value.get_ik()
            depth_value = measurement_value.get_depth()
            values_list.append(ik_value)
            depths_list.append(depth_value)
        
        
        ik_at_depth = self.interpolate_values_at_depth(validated_depth, depths_list, values_list)
        
        return ik_at_depth        
    
        
        
        

    def interpolate_values_at_depth(self, depth, depths_list=[], values_list=[]):
        '''
        INTERPOLATE VALUES AT DEPTH
        Essentially, given an array of "x" (validated_depth) and "y" values, interpolates "y" value at specified validated_depth.
        
        
        
        '''

        
        # Uses http://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html   
        validated_depth = self.validate_depth(depth)
        
        max_depth_given = max(depths_list)
        min_depth_given = min(depths_list)
        
        if(validated_depth>max_depth_given):            
            print "depth is",validated_depth, "cannot interpolate outside the range of measurements given. setting to max."
            validated_depth= max_depth_given
        elif(min_depth_given<min_depth_given):
            print "depth is",validated_depth, "cannot interpolate outside the range of measurements given. setting to min.."
            validated_depth= min_depth_given            
            
        
        # get interpolation function
        x = depths_list
        y = values_list 
        f = interp1d(x, y)
        
        #magic from # Uses http://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html
        #SPLINES....!!!
        tck = interpolate.splrep(x, y, s=0)
        xnew = [validated_depth]
        spline_interpolated = interpolate.splev(xnew, tck, der=0) #0th derivative
        linear_interpolated = f(validated_depth)         
        
        
        

#         value_at_depth = spline_interpolated[0] #TODO: inefficient to get the whole array and return just one.
        value_at_depth = linear_interpolated
        return value_at_depth        
    
    
    
    time_interval = property(get_time_interval, set_time_interval, del_time_interval, "time_interval's docstring")

    
    def calculate_depths_of_specific_light_percentages(self, light_penetration_depths):
        '''
        given a list of light penetration depths returns the depth in meters needed for each of those light penetration levels.
        @rtype: list 
        '''
        depths = []
        for light_penetration_depth in light_penetration_depths:
            depth_m_of_light_penetration = self.calculate_depth_of_specific_light_percentage(light_penetration_depth)
            depths.append(depth_m_of_light_penetration)
        return depths
    
    
     






def main():
    print "hello world"
    m0 = BenthicPhotoSynthesisMeasurement(0.0, 14.75637037, 404.943)
    m1 = BenthicPhotoSynthesisMeasurement(1.0, 25.96292587, 307.6793317)
    m2 = BenthicPhotoSynthesisMeasurement(2.0, 57.98165587, 238.6559726)
    m3 = BenthicPhotoSynthesisMeasurement(3.0, 47.35232783, 189.673406)
    m4 = BenthicPhotoSynthesisMeasurement(4.0, 36.7229998, 154.9128285)
    m5 = BenthicPhotoSynthesisMeasurement(5.0, 33.63753108, 130.2449143)
    m6 = BenthicPhotoSynthesisMeasurement(6.0, 26.8494999, 112.7392791)
    m7 = BenthicPhotoSynthesisMeasurement(7.0, 20.06146872, 100.3163696)
    m8 = BenthicPhotoSynthesisMeasurement(8.0, 16.976, 91.50042668)
    m9 = BenthicPhotoSynthesisMeasurement(9.0, 15.45920354, 85.24417497)
    m10 = BenthicPhotoSynthesisMeasurement(10.0, 11.7585159, 80.80441327)
    m11 = BenthicPhotoSynthesisMeasurement(11.0, 7.148489714, 77.6537274)
    m12 = BenthicPhotoSynthesisMeasurement(12.0, 2.903677594, 75.41783679)
    m13 = BenthicPhotoSynthesisMeasurement(13.0, 0.2986321643, 73.83113249)
    
    
    measurement_list = [m0, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12, m13]
    areas = {0:50, 5:25, 13.4:10}
    
    pond_shape_instance = BathymetricPondShape(areas)
       
    
    p = Pond("lake_ID", 360, 12.0, 1440.0, 0.3429805354, pond_shape_instance, measurement_list, measurement_list)
    
    depth_of_one_percent_light = p.calculate_depth_of_specific_light_percentage(.01)
    
    print "depth of 1% light is ", depth_of_one_percent_light
    proportional_light = p.calculate_light_proportion_at_depth(depth_of_one_percent_light)
    print "%light of depth ", depth_of_one_percent_light, " is ", proportional_light
    

    
    max_depth = p.get_max_depth()
    print "max depth is ", max_depth
    
    current_depth = 0
    depth_interval_meters = 0.5
    while(current_depth < max_depth):
        print "current depth is ", current_depth
        print "benthic pmax at this depth is: ", p.get_benthic_pmax_at_depth(current_depth)     
        print "benthic ik at this depth is: ", p.get_benthic_ik_at_depth(current_depth)   
        current_depth += depth_interval_meters
    
    littoral_area = p.calculate_total_littoral_area()
    print "littoral area is (should be ~40): ", littoral_area
    
    depth=5
    depth_interval = depth
    sediment_area = p.pond_shape_object.get_sediment_surface_area_at_depth(depth, depth_interval)
    
    
    print "sediment area at depth ", depth, " with interval = ", depth_interval, " is ", sediment_area
    
    f_area1 = p.pond_shape_object.get_fractional_sediment_area_at_depth(depth, littoral_area, depth_interval)
    
    print "f_area, same parameters. Should be 25/40 = 0.625: ", f_area1
    
    
    depth=13.4
    depth_interval = 13.4-5
    sediment_area = p.pond_shape_object.get_sediment_surface_area_at_depth(depth, depth_interval)
    
    
    print "sediment area at depth ", depth, " with interval = ", depth_interval, " is ", sediment_area
    f_area2 = p.pond_shape_object.get_fractional_sediment_area_at_depth(depth, littoral_area, depth_interval)
    
    print "f_area, same parameters. Should be 15/40 = 0.375: ", f_area2
    
    print "f_area1+f_area2: ", f_area1+f_area2
        




if __name__ == "__main__":
    main()
