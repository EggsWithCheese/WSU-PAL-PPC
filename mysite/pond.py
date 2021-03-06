# -*- coding: utf-8 -*-
"""
Created on Thu Jun 05 09:38:17 2014

@author: cdleong
"""
import traceback
import math as mat
import numpy as np
from pond_shape import PondShape
from benthic_photosynthesis_measurement import BenthicPhotosynthesisMeasurement
from bathymetric_pond_shape import BathymetricPondShape
from scipy.interpolate import interp1d
from phytoplankton_photosynthesis_measurement import PhytoPlanktonPhotosynthesisMeasurement











class Pond(object):

    ###################################
    # CONSTANTS
    ###################################
    MINIMUM_VALID_YEAR = 1 #If you want to do lakes from year 0 or B.C., you code it.
    MAXIMUM_VALID_YEAR = 9999 #I'm sorry, people in the year 10000 A.D., and/or time travellers.
    
    MINIMUM_VALID_DAY = 0  # New Year's Day
    MAXIMUM_VALID_DAY = 366  # New Year's Eve in a leap year.

    MINIMUM_LENGTH_OF_DAY = 0.0  # north of the arctic circle and south of the antarctic one, this is possible during winter.
    MAXIMUM_LENGTH_OF_DAY = 24.0003  # north of the arctic circle and south of the antarctic one, this is possible during summer, if there's a leap second

    MINIMUM_NOON_SURFACE_LIGHT = 0.0  # Total darkness. TODO: will this cause divide-by-zero errors?
    MAXIMUM_NOON_SURFACE_LIGHT = 1000000.0  # normally it's in the range of ~1000-2000. A 1000x increase, I'm pretty sure, would sterilize the lake. And probably the Earth. According to http://autogrow.com/general-info/light-measurement, the highest it generally gets on Earth is 2000. Don't wanna exclude nuclear weapons going off over lakes, though, you know?


    MINIMUM_LIGHT_ATTENUATION_COEFFICIENT = 0.0  # totally, perfectly clear. Units in inverse meters. M^-1 #TODO: will this cause divide-by-zero errors?
    MAXIMUM_LIGHT_ATTENUATION_COEFFICIENT = 100  # Close enough to totally opaque to make no practical difference. At this level, light goes from 100% at depth 0 to 0.005% at 10 centimeters. No meaningful photosynthesis is likely to be going on in this lake.

    PHOTIC_ZONE_LIGHT_PENETRATION_LEVEL_LOWER_BOUND = 0.01  # 1% light penetration is the definition of the photic zone from various sources, including Vadeboncoeur 2008, and http://limnology.wisc.edu/courses/zoo316/REVIEW%20OF%20A%20FEW%20MAJOR%20CONCEPTS.html

    MAXIMUM_LAKE_ID_LENGTH = 140  # value picked arbitrarily during specification process. I chose it because I had Twitter on the mind. Possibly too long. 50 characters would give us enough characters for "Lake Chargoggagoggmanchaoggagoggchaubunaguhgamaugg", the longest lake name in the world...

    MAXIMUM_NUMBER_OF_THERMAL_LAYERS = 3 #epilimnion, hypolimnion, metalimnion

    DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS = 0.1  # ten centimeters, 0.1 meters. Arbitrary.

    DEFAULT_FREEZE_DAY = 349  # December 15 #arbitrary default value, based on median from http://www.epa.gov/climatechange/pdfs/CI-snow-and-ice-2014.pdf
    DEFAULT_THAW_DAY = 135  # May 15 #arbitrary default value, based on median from http://www.epa.gov/climatechange/pdfs/CI-snow-and-ice-2014.pdf
    
    BASE_TIME_UNIT = 1 #hours


    ###################################
    # VARIABLES
    ###################################

    # identifying variables, aka Primary Key
    year = 1900 
    lake_ID = ""  # invalid lake ID I'm assuming. #TODO: check.
    day_of_year = 0  # day of year 0-366


    # General pond information. Light/photosynthesis
    length_of_day = 15  # hours of sunlight
    noon_surface_light = 1500  # micromol*m^(-2)*s^(-1 ) (aka microEinsteins?)
    light_attenuation_coefficient = 0.05  # aka "kd"

    # shape object. Holds information regarding the shape of the lake. Methods include area at depth, volume at depth, etc.
    pond_shape_object = PondShape()

    # benthic photosynthesis data list
    benthic_photosynthesis_measurements = []

    # phytoplankton photosynthesis data list #TODO: everything to do with this
    phytoplankton_photosynthesis_measurements = []


    # default intervals for calculations is quarter-hours
    time_interval = 0.25




    ############################
    # CONSTRUCTOR
    ###########################
    def __init__(self,
                 year = 1900,
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
        @param lake_ID: string
        @param day_of_year: integer day of year
        @param length_of_day: float number of hours
        @param noon_surface_light: float 
        @param light_attenuation_coefficient: float
        @param pond_shape_object: a PondShape object
        @param benthic_photosynthesis_measurements: a list of BenthicPhotoSynthesisMeasurements
        @param phytoplankton_photosynthesis_measurements:  a list of PhyttoplanktonPhotoSynthesisMeasurements
        '''
        self.set_year(year)
        self.set_lake_id(lake_ID)
        self.set_day_of_year(day_of_year)
        self.length_of_day = length_of_day
        self.noon_surface_light = noon_surface_light
        self.light_attenuation_coefficient = light_attenuation_coefficient
        self.set_pond_shape(pond_shape_object)
        self.set_benthic_photosynthesis_measurements(benthic_photosynthesis_measurements)
        self.set_phytoplankton_photosynthesis_measurements(phytoplankton_photosynthesis_measurements)
        self.set_time_interval(time_interval)





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
        @return: a valid value in the range (max_value,min_value), inclusive
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

    def validate_year(self, year):
        '''
        Checks if year is set to reasonable value. If not, returns minimum or maximum possible reasonable value (whichever is closest)
        @param year:
        @return: A valid value in the range (Pond.MAXIMUM_VALID_YEAR, Pond.MINIMUM_VALID_YEAR), inclusive
        @rtype: int  
        '''
        return self.validate_numerical_value(year, Pond.MAXIMUM_VALID_YEAR, Pond.MINIMUM_VALID_YEAR)
    
    def validate_day_of_year(self, day_of_year=0):
        '''

        @param day_of_year: the day of year the measurement was made.
        @return: a valid value in the range (Pond.MAXMUM_VALID_DAY,Pond.MINIMUM_VALID_DAY), inclusive
        @rtype: int
        '''
        return self.validate_numerical_value(day_of_year, Pond.MAXIMUM_VALID_DAY, Pond.MINIMUM_VALID_DAY)

    def validate_length_of_day(self, length_of_day=0.0):
        '''
        Checks if length_of_day is set to reasonable value. If not, returns minimum or maximum possible reasonable value (whichever is closest)
        @param length_of_day:
        @return: a valid value in the range (Pond.MAXIMUM_LENGTH_OF_DAY,Pond.MAXIMUM_LENGTH_OF_DAY), inclusive
        @rtype:  float
        '''
        return self.validate_numerical_value(length_of_day, Pond.MAXIMUM_LENGTH_OF_DAY, Pond.MINIMUM_LENGTH_OF_DAY)

    def validate_proportional_value(self, proportional_value):
        '''
        Checks if a proportional value is actually within a reasonable range. If not, returns minimum or maximum possible reasonable value (whichever is closest)
        @param proportional_value:
        @return: a value in the range (0.0, 1.0) inclusive
        @rtype: float
        '''
        validated_proportional_value = self.validate_numerical_value(proportional_value, 1.0, 0.0)
        return validated_proportional_value

    def validate_depth(self, depth=0.0):
        '''
        Checks if depth is set to reasonable value. If not, returns minimum or maximum possible reasonable value (whichever is closest)
        @param depth:
        @return: a depth in the range (0.0 (the surface), and the max depth of the lake) inclusive 
        @rtype: float
        '''
        pond_shape_object = self.get_pond_shape()
        validated_depth = pond_shape_object.validate_depth(depth)
        return validated_depth

    def validate_noon_surface_light(self, noon_surface_light=0.0):
        '''
        Checks if noon_surface_light is set to plausible value. If not, returns minimum or maximum possible reasonable value (whichever is closest)
        @param noon_surface_light:
        @return: a value in the range (Pond.MAXIMUM_NOON_SURFACE_LIGHT, Pond.MINIMUM_NOON_SURFACE_LIGHT) inclusive
        @rtype: float
        '''
        validated_noon_surface_light = self.validate_numerical_value(noon_surface_light, Pond.MAXIMUM_NOON_SURFACE_LIGHT, Pond.MINIMUM_NOON_SURFACE_LIGHT)
        return validated_noon_surface_light

    def validate_light_attenuation_coefficient(self, light_attenuation_coefficient):
        '''
        Checks if light attenuation is set to reasonable value. If not, returns minimum or maximum possible reasonable value (whichever is closest)
        @param light_attenuation_coefficient: 
        @return: a value in the range (Pond.MAXIMUM_LIGHT_ATTENUATION_COEFFICIENT, Pond.MINIMUM_LIGHT_ATTENUATION_COEFFICIENT) inclusive
        @rtype: float
        '''
        validated_light_attenuation_coefficient = self.validate_numerical_value(light_attenuation_coefficient, Pond.MAXIMUM_LIGHT_ATTENUATION_COEFFICIENT, Pond.MINIMUM_LIGHT_ATTENUATION_COEFFICIENT)
        return validated_light_attenuation_coefficient

    def validate_types_of_all_items_in_list(self, items=[], desired_type=object):
        '''
        Checks if every item in a list is of the correct type of object.
        @param items:
        @param desired_type:
        @return: True if all items in the list are the given type. False otherwise.
        @rtype: boolean
        '''
        all_valid = False
        if(all(isinstance(item, desired_type) for item in items)):
            all_valid = True
        else:
            all_valid = False
        return all_valid


    def validate_time(self, time):
        '''
        Checks if time is set to reasonable value. If not, returns minimum or maximum possible reasonable value (whichever is closest)
        Differs from validate_length_of_day in that it checks the value of time against the length of day of this lake.
        @param light_attenuation_coefficient: 
        @return: a value in the range (self.get_length_of_day(), Pond.Pond.MINIMUM_LENGTH_OF_DAY) inclusive
        @rtype: float
        '''
        length_of_day = self.get_length_of_day()
        validated_time = self.validate_numerical_value(time, length_of_day, Pond.MINIMUM_LENGTH_OF_DAY)
        return validated_time






    #######################
    # GETTERS
    #######################
    def get_key(self):
        '''
        Get Key
        Used for convenient identification of ponds. So long as none of them has the same year, ID, and day, it works.
        @return: year + lake_id + day
        @rtype: string 
        '''
        string1 = str(self.get_year())
        string2 = str(self.get_lake_id())
        string3 = str(self.get_day_of_year())
        return str(string1+string2+string3) #TODO:thisisridiculous
    
    def get_year(self):
        '''
        Get Year
        @return: year
        @rtype: int
        '''
        return int(self.__year)
    
    
    def get_lake_id(self):
        '''
        Get Lake ID
        @return: the ID of the lake.
        @rtype: string
        '''
        return self.__lake_ID


    def get_day_of_year(self):
        '''
        Get Day of Year
        @return: the day of on which measurements occurred.
        @rtype: float
        '''
        #TODO: fix this. only made it float so I could fix a temporary issue with the test data.
        return int(self.__day_of_year)


    def get_length_of_day(self):
        '''
        Get Length Of Day
        @return: the length of day, in hours, on the day of measurements.
        @rtype: float
        '''
        return self.__length_of_day


    def get_noon_surface_light(self):
        '''
        Get Noon Surface Light
        @return: The surface light intensite at solar noon, in micromoles per square meter per second(umol*m^-2*s^-1)
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
        @rtype: list containing BenthicPhotosynthesisMeasurement objects
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
        '''
        Get Max Depth
        Calls get max depth method in PondShape instance.
        @return: maximum depth of lake
        '''
        return self.get_pond_shape().get_max_depth()



    def get_time_interval(self):
        '''
        Get Time Interval
        Get the time interval used for calculations. 
        @rtype: float
        '''
        return self.__time_interval
    
    def get_list_of_times(self):
        '''
        Gets a list of the times of day used for calculations. 
        
        Example: if the day length was 2 hours, and the time interval was 0.25 (quarter-hours), this would return
        [0.0,0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0]
        @rtype: list 
        '''
        start_time = 0.0
        end_time = self.get_length_of_day()
        time_interval = self.get_time_interval()
        time_list = []
        time =start_time
        while time<=end_time:
            time_list.append(time)
            time+=time_interval
            
            
        return time_list
        


    #######################
    # SETTERS
    #######################
    
    def set_year(self, year):
        '''
        Set year
        Validates it first using validate_year
        '''
        self.__year = self.validate_year(year)    

    def set_lake_id(self, lake_id):
        '''
        Set Lake ID
        @param lake_id:
        '''
        self.__lake_ID = lake_id


    def set_day_of_year(self, day_of_year):
        '''
        Set Day Of Year
        Validates the value
        @param day_of_year:
        '''
        validated_day_of_year = self.validate_day_of_year(day_of_year)
        self.__day_of_year = validated_day_of_year


    def set_length_of_day(self, length_of_day):
        '''
        Set Length Of Day
        Validates the value
        @param length_of_day:
        '''
        validated_length_of_day = self.validate_length_of_day(length_of_day)
        self.__length_of_day = validated_length_of_day


    def set_noon_surface_light(self, noon_surface_light):
        '''
        Set Noon Surface Light
        Validates the value
        @param noon_surface_light:
        '''
        validated_light = self.validate_noon_surface_light(noon_surface_light)
        self.__noon_surface_light = validated_light


    def set_light_attenuation_coefficient(self, light_attenuation_coefficient):
        '''
        Set Light Attenuation Coefficient
        Validates the value
        @param light_attenuation_coefficient: Also known as light extinction coefficient, or just kd. Units in inverse meters.
        '''
        validated_light_attenuation_coefficient = self.validate_light_attenuation_coefficient(light_attenuation_coefficient)
        self.__light_attenuation_coefficient = validated_light_attenuation_coefficient



    def set_time_interval(self, time_interval):
        '''
        Set Time Interval
        @param time_interval: fractional hours. For example, 0.5 = half hours, 0.25 = 15 minutes. 
        '''
        self.__time_interval = time_interval

    def set_pond_shape(self, pond_shape_object):
        '''
        Set Time Interval
        Validates the value
        @param pond_shape_object: a PondShape object of some type. So long as it extends PondShape, it should work. 
        '''
        if(isinstance(pond_shape_object, PondShape)):
            self.pond_shape_object = pond_shape_object
        else:
            raise Exception("cannot set pond shape. Invalid type")



    def set_benthic_photosynthesis_measurements(self, values=[]):
        '''
        Set Benthic Photosynthesis Measurements
        Given a list of BenthicPhotosynthesisMeasurement objects, replaces the current list with values.
        Validates the list using validate_types_of_all_items_in_list()
        '''
        all_valid = self.validate_types_of_all_items_in_list(values, BenthicPhotosynthesisMeasurement)
        if(all_valid):
            self.__benthic_photosynthesis_measurements = values
        else:
            raise Exception("ERROR: all values in benthic_photosynthesis_measurements must be of type BenthicPhotosynthesisMeasurement")


    def set_phytoplankton_photosynthesis_measurements(self, values=[]):
        '''
        Set Phytoplankton Photosynthesis Measurements
        Given a list of PhytoPlanktonPhotosynthesisMeasurement objects, replaces the current list with values.
        Validates the list using validate_types_of_all_items_in_list()
        Also makes sure that there are less than or equal to MAXIMUM_NUMBER_OF_THERMAL_LAYERS measurements.
        '''
        # TODO: use a dict to ensure 3 unique layers.
        all_valid = self.validate_types_of_all_items_in_list(values, PhytoPlanktonPhotosynthesisMeasurement)
        length_valid = len(values) <= self.MAXIMUM_NUMBER_OF_THERMAL_LAYERS

        if(not all_valid):
            raise Exception("ERROR: all values in phytoplankton_photosynthesis_measurements must be of type PhytoPlanktonPhotosynthesisMeasurement")
        elif(not length_valid):
            raise Exception("ERROR: there must be 0 to 3 thermal layers")
        else:
            self.__phytoplankton_photosynthesis_measurements = values





    #############################
    # DELETERS
    #############################
    
    def del_year(self):
        del self.__year    

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


    def del_time_interval(self):
        del self.__time_interval


    ########################################
    # Properties
    ########################################    
    #TODO: write decent docstrings
    year = property(get_year, set_year, del_year, "year's docstring")
    lake_ID = property(get_lake_id, set_lake_id, del_lake_id, "lake_ID's docstring")
    day_of_year = property(get_day_of_year, set_day_of_year, del_day_of_year, "day_of_year's docstring")
    length_of_day = property(get_length_of_day, set_length_of_day, del_length_of_day, "length_of_day's docstring")
    noon_surface_light = property(get_noon_surface_light, set_noon_surface_light, del_noon_surface_light, "noon_surface_light's docstring")
    light_attenuation_coefficient = property(get_light_attenuation_coefficient, set_light_attenuation_coefficient, del_light_attenuation_coefficient, "light_attenuation_coefficient's docstring")
    benthic_photosynthesis_measurements = property(get_benthic_photosynthesis_measurements, set_benthic_photosynthesis_measurements, del_benthic_photosynthesis_measurements, "benthic_photosynthesis_measurements's docstring")
    phytoplankton_photosynthesis_measurements = property(get_phytoplankton_photosynthesis_measurements, set_phytoplankton_photosynthesis_measurements, del_phytoplankton_photosynthesis_measurements, "phytoplankton_photosynthesis_measurements's docstring")
    time_interval = property(get_time_interval, set_time_interval, del_time_interval, "time_interval's docstring")




    ########################################
    # Appenders/mutators
    ########################################
    def add_benthic_measurement(self, measurement=BenthicPhotosynthesisMeasurement):
        if(isinstance(measurement, BenthicPhotosynthesisMeasurement)):
            self.benthic_photosynthesis_measurements.append(measurement)
        else:
            raise Exception("ERROR: cannot add measurement to benthic measurements list - measurement must be of type BenthicPhotosynthesisMeasurement")

    def add_benthic_measurement_if_photic(self, measurement):
        z1Percent = self.calculate_depth_of_specific_light_percentage(self.PHOTIC_ZONE_LIGHT_PENETRATION_LEVEL_LOWER_BOUND)
        if(measurement.get_depth() <= z1Percent):
            self.add_benthic_measurement(measurement)
        else:
            raise Exception("measurement not within photic zone")


    def add_phytoplankton_measurement(self, measurement=PhytoPlanktonPhotosynthesisMeasurement):
        if(isinstance(measurement, PhytoPlanktonPhotosynthesisMeasurement)):
            if(len(self.phytoplankton_photosynthesis_measurements) > 0):
                existing_measurement = next((i for i in self.phytoplankton_photosynthesis_measurements if (i.get_thermal_layer() == measurement.get_thermal_layer())), None)  # source: http://stackoverflow.com/questions/7125467/find-object-in-list-that-has-attribute-equal-to-some-value-that-meets-any-condi
                if(existing_measurement is not None):
                    index = measurement.get_thermal_layer() - 1
                    self.phytoplankton_photosynthesis_measurements.remove(existing_measurement)
                    try:
                        self.phytoplankton_photosynthesis_measurements.insert(index, measurement)
                    except TypeError:
                        error = "TypeError: index is ", index, " and measurement is ", measurement, " for pond ", self.get_lake_id(), " day ", self.get_day_of_year()
                        raise Exception(error)


            self.phytoplankton_photosynthesis_measurements.append(measurement)
        else:
            raise Exception("ERROR: cannot add measurement to benthic measurements list - measurement must be of type PhytoPlanktonPhotosynthesisMeasurement")


    def remove_benthic_measurement(self, measurement=BenthicPhotosynthesisMeasurement):
        self.benthic_photosynthesis_measurements.remove(measurement)

    def update_shape(self, other_pond_shape):
        our_shape = self.get_pond_shape()
        if(isinstance(other_pond_shape, BathymetricPondShape)):
            our_shape.update_shape(other_pond_shape)
            self.pond_shape_object = our_shape

    ############################################
    ############################################
    # # SCIENCE FUNCTIONS
    # # This section is where the science occurs.
    ############################################
    ############################################


    ###########################################################
    # BENTHIC PHOTO METHODS
    ###########################################################

    ##############################
    # BENTHIC PRIMARY PRODUCTIVITY
    ##############################
    def calculate_daily_whole_lake_benthic_primary_production_m2(self, depth_interval=DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS, use_littoral_area=True):
        '''
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        Almost everything else in this entire project works to make this method work.
        #TODO: (someday) allow specification of littoral or surface area
        #TODO: (someday) user-specified depth interval.
        @return: Benthic Primary Production, mg C per meter squared, per day.
        @rtype: float
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        '''

        time_interval = self.get_time_interval()
        length_of_day = self.get_length_of_day()  # TODO: Fee normalized this around zero. Doesn't seem necessary, but might affect the periodic function.

        
        benthic_primary_production_answer = 0.0  # mg C per day
        current_depth_interval = 0.0
        previous_depth = 0.0
        current_depth = 0.0 
        total_littoral_area=0.0
        total_littoral_area = self.calculate_total_littoral_area()
        total_surface_area = self.get_pond_shape().get_water_surface_area_at_depth(0.0)

        # for each depth interval #TODO: integration over whole lake?
        while current_depth < self.calculate_photic_zone_lower_bound():
            bpprz = 0.0  # mg C* m^-2 *day

            # depth interval calculation
            previous_depth = current_depth
            current_depth += depth_interval
            current_depth_interval = current_depth - previous_depth




            area = self.get_pond_shape().get_sediment_area_at_depth(current_depth, current_depth_interval)

            try:
                ik_z = self.get_benthic_ik_at_depth(current_depth)
                benthic_pmax_z = self.get_benthic_pmax_at_depth(current_depth)
            except: 
                raise 
            
            if(True == use_littoral_area):
                f_area = area / total_littoral_area  # TODO: these add up to 1.0, right?
            else:
                f_area = area / total_surface_area


            # for every time interval
            t = 0.0  # start of day
            while t < length_of_day:
                bpprzt = 0.0
                izt = self.calculate_light_at_depth_and_time(current_depth, t)
                bpprzt = self.calculate_benthic_primary_production_z_t(izt, benthic_pmax_z, ik_z)

                bpprz += bpprzt

                t += time_interval
            bpprz = bpprz / (self.BASE_TIME_UNIT / time_interval)  # account for the fractional time interval. e.g. dividing by 1/0.25 is equiv to dividing by 4
            weighted_bpprz = bpprz * f_area  # normalizing




            benthic_primary_production_answer += weighted_bpprz
            
        return benthic_primary_production_answer






    def get_benthic_pmax_at_depth(self, depth=0.0):
        '''
        Get Benthic Pmax At Depth
        Uses interpolation to get the pmax value at the specified depth, if not known. 
        Validates depth first.
        @return: value of pmax at specified depth.
        @rtype: float
        '''
        # if depth is lower than the depth of 1% light, pmax approaches zero.
        if(self.check_if_depth_in_photic_zone(depth) == False):
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
        Get Benthic Ik At Depth
        Uses interpolation to get the Ik value at the specified depth, if not known. 
        Validates depth first.
        @return: value of pmax at specified depth.
        @rtype: float
        '''
        validated_depth = self.validate_depth(depth)


        values_list = []
        depths_list = []
        for measurement_value in self.get_benthic_photosynthesis_measurements():
            ik_value = measurement_value.get_ik()
            depth_value = measurement_value.get_depth()
            values_list.append(ik_value)
            depths_list.append(depth_value)

        try:
            ik_at_depth = self.interpolate_values_at_depth(validated_depth, depths_list, values_list)
        except:
            raise
            
        return ik_at_depth

    def calculate_benthic_primary_production_z_t(self, light_at_time_and_depth, benthic_pmax_z_t, benthic_ik_z_t):
        '''
        Benthic primary production rate at a specific depth and time
        @return: 
        @rtype: float
        '''
        bpprzt = benthic_pmax_z_t * np.tanh(light_at_time_and_depth / benthic_ik_z_t)
        return bpprzt

    def get_benthic_measurements_sorted_by_depth(self):
        '''
        Sorted BenthicPhotosynthesisMeasurement list, by depth.
        @return: sorted benthic measurements
        @rtype: list of BenthicPhotosynthesisMeasurement objects.
        '''
        # http://stackoverflow.com/questions/403421/how-to-sort-a-list-of-objects-in-python-based-on-an-attribute-of-the-objects
        unsorted_measurements = self.get_benthic_photosynthesis_measurements()
        sorted_measurements = sorted(unsorted_measurements, key=lambda x: x.get_depth(), reverse=False)
        return sorted_measurements

    ###########################################################
    # PHYTO PHOTO METHODS
    ###########################################################


    def calculate_daily_whole_lake_phytoplankton_primary_production_m2(self, 
                                                                             depth_interval=DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS, 
                                                                             use_photoinhibition=None):
        '''
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        Calculate Daily Whole-lake Phytoplankton Primary Production
        Almost everything else in this entire project works to make this method work.
        #TODO: (someday) allow specification of littoral or surface area
        #TODO: (someday) user-specified depth interval.
        @return: Benthic Primary Production, mg C per meter squared, per day.
        @rtype: float
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        '''

        

        layer_depths = self.get_thermal_layer_depths()
        layer_upper_bound = 0.0
        layer_lower_bound = 0.0
        layer_pp_list = []
        
        for layer_depth in layer_depths:
            layer_lower_bound = layer_depth

                
            
            layer_pp_daily_m2 = self.calculate_phytoplankton_primary_production_rate_in_interval(layer_upper_bound, layer_lower_bound, depth_interval, use_photoinhibition)
            layer_pp_list.append(layer_pp_daily_m2)                          
            layer_upper_bound = layer_lower_bound #set the new upper bound for the next round of calculations using the current lower bound.
            
         
        pp_lake_daily_total_m2 = sum(layer_pp_list)
        return pp_lake_daily_total_m2  # mgC/m^2/day

    def calculate_hourly_phytoplankton_primary_production_rates_list_over_whole_day_in_thermal_layer(self, 
                                                                                                     layer = 0, 
                                                                                                     depth_interval=DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS,
                                                                                                     use_photoinhibition=None,
                                                                                                     convert_to_m2 = False):
        '''
        Used for graphing hourly rates over the course of a day, for a layer.
        @param layer: thermal layer of pond. 0=epilimnion, 1 = metalimnion, 2 = hypolimnion 
        @param depth_interval: the depth interval for calculations
        @param use_photoinhibition: whether or not to use the photoinhibition equation.
        @param convert_to_m2: whether or not to convert the resulting values to (per meter squared) instead of (per meter cubed) 
        @return: list of hourly rates, over the course of a day. Length should be (length of day)/(time_interval)
        '''
        MAX_INDEX = self.MAXIMUM_NUMBER_OF_THERMAL_LAYERS-1
        MIN_INDEX  = 0
        
        validated_layer=self.validate_numerical_value(layer, MAX_INDEX, MIN_INDEX) #0=epilimnion, 1=metalimnion, 2 = hypolimnion
        layer_depths = self.get_thermal_layer_depths()

        
        #say layer_depths contains [5.0,7.0,16.0]. 
        #if validate_layer = 0, We would want layer_upper_bound = 0.0, layer_lower_bound = 5.0 (layer_depths[0])
        #if validate_layer = 1, We would want layer_upper_bound = 5.0 (layer_depths[0]), layer_lower_bound = 7.0 (layer_depths[1])
        #if validate_layer = 2, We would want layer_upper_bound = 7.0 (layer_depths[1]), layer_lower_bound = 16.0 (layer_depths[2])
        
        layer_upper_bound = 0.0
        if(validated_layer>0): #I just feel there's a more elegant way to do this.
            layer_upper_bound=layer_depths[validated_layer-1]
        layer_lower_bound = layer_depths[validated_layer]
        pp_list = self.calculate_hourly_phytoplankton_primary_production_rates_list_over_whole_day_in_interval(layer_upper_bound, layer_lower_bound, depth_interval, use_photoinhibition, convert_to_m2)
        return pp_list
        
        
        
                  
          
         
        
        
        
        
        
        

    def calculate_hourly_phytoplankton_primary_production_rates_list_over_whole_day_in_interval(self, 
                                                                    interval_upper_bound, 
                                                                    interval_lower_bound, 
                                                                    depth_interval=DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS, 
                                                                    use_photoinhibition=None,
                                                                    convert_to_m2 = False):
        '''
        Used for graphing hourly rates over the course of a day, but over a depth interval instead of a thermal layer.
        @param interval_upper_bound: depth in meters 
        @param interval_lower_bound: depth in meters
        @param depth_interval: the depth interval for calculations
        @param use_photoinhibition: whether or not to use the photoinhibition equation.
        @param convert_to_m2: whether or not to convert the resulting values to (per meter squared) instead of (per meter cubed) 
        @return: list of hourly rates, over the course of a day. Length should be (length of day)/(time_interval)
        '''
        if (use_photoinhibition is None):          
            beta_parameter =self.get_phyto_beta_at_depth(interval_lower_bound)   
            if(0==beta_parameter):
                use_photoinhibition = False
            else: 
                use_photoinhibition = True
      

        # TODO: validate interval
        time_interval = self.get_time_interval()  # hours
        length_of_day = self.get_length_of_day()
          
        max_depth = self.get_pond_shape().get_max_depth()
        total_volume = self.get_pond_shape().get_volume_above_depth(max_depth, depth_interval)
        layer_depth_interval = interval_lower_bound - interval_upper_bound  # "deeper" is bigger magnitude, so instead of upper-lower we do lower - upper 

        hourly_pp_list = []
        current_time = 0.0  # start of day
#         pp_layer_daily_total_hw_m3 = 0.0
        
        while current_time <= length_of_day:
            
            
            depth_m = interval_upper_bound #meters from surface.
            pp_total_in_thermal_layer_at_time_t_hw_m3 = 0.0 #primary production in layer, mg C/ m^3 / hour, or mgC*m^-3*hr-1
            
            while depth_m <= interval_lower_bound:
                
                light_at_depth_z_time_t = self.calculate_light_at_depth_and_time(depth_m, current_time)  # umol*m^-2*s^-1
                interval_volume_m3 = self.get_pond_shape().get_volume_at_depth(depth_m, depth_interval)  # m^3
                fractional_volume = interval_volume_m3 / total_volume
                pp_rate_at_depth_z_time_t_m3 = self.calculate_phytoplankton_primary_productivity(light_at_depth_z_time_t, depth_m, use_photoinhibition)  # mgC*m^-3*hr^-1, or mgC per meter cubed per hour
                pp_total_at_depth_z_time_t_m3_in_one_time_unit = pp_rate_at_depth_z_time_t_m3 * self.BASE_TIME_UNIT  # mgC*m^-3*hr^-1 * 1 hour = mgC*m^-3. This line usually multiplies by 1, changing nothing.
                pp_total_at_depth_z_time_t_hw_m3 = pp_total_at_depth_z_time_t_m3_in_one_time_unit * fractional_volume  # mgC*m^-3, hypsometrically weighted
                pp_total_in_thermal_layer_at_time_t_hw_m3 += pp_total_at_depth_z_time_t_hw_m3 #mgC*m^-3 #THIS IS WHAT I CHECKED TO TEST AGAINST NTL LTER DATABASE                                
                depth_m += depth_interval
                    
                    
            

            if(current_time%time_interval==0):
                hourly_pp_list.append(pp_total_in_thermal_layer_at_time_t_hw_m3)
#             pp_layer_daily_total_hw_m3 += pp_total_in_thermal_layer_at_time_t_hw_m3   #Units are still mgC*m^-3               
            


            current_time += time_interval
        
        
        
#       
        if(convert_to_m2):
            hourly_pp_list = [value*layer_depth_interval for value in hourly_pp_list] #multiply by the depth interval of the layer to convert to m2
                
        return hourly_pp_list  # mgC/m^2/day
        


    def calculate_phytoplankton_primary_production_rate_in_interval(self, 
                                                                    interval_upper_bound, 
                                                                    interval_lower_bound, 
                                                                    depth_interval=DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS, 
                                                                    use_photoinhibition=None):
        '''
        Allows calculation of daily primary production in any valid depth interval
        @param interval_upper_bound: depth in meters 
        @param interval_lower_bound: depth in meters
        @param depth_interval: the depth interval for calculations
        @param use_photoinhibition: whether or not to use the photoinhibition equation.                        
        '''
        
        if (use_photoinhibition is None):          
            beta_parameter =self.get_phyto_beta_at_depth(interval_lower_bound)   
            if(0==beta_parameter):
                use_photoinhibition = False
            else: 
                use_photoinhibition = True


        # TODO: validate interval

          
        layer_depth_interval = interval_lower_bound - interval_upper_bound  # "deeper" is bigger magnitude, so instead of upper-lower we do lower - upper 


        
        
        #We have "per hour" calculated multiple times per hour. We must correct for this in our summation.
        time_interval = self.get_time_interval()  # hours        
        time_interval_correction_factor = (self.BASE_TIME_UNIT / time_interval)  # (hr/hr) Account for the fractional time interval. e.g. dividing by 1/0.25 is equiv to dividing by 4
        ppr_over_time_in_interval_list = self.calculate_hourly_phytoplankton_primary_production_rates_list_over_whole_day_in_interval(interval_upper_bound, interval_lower_bound, depth_interval, use_photoinhibition)
        pp_layer_daily_total_hw_m3 = sum(ppr_over_time_in_interval_list)
        
        
        pp_layer_daily_total_hw_time_corrected_m3 = pp_layer_daily_total_hw_m3/time_interval_correction_factor
        

        
        #convert to m^-2
        #multiplying by the vertical distance from the top to the bottom of the thermal layer is what was, apparently, 
        #done to convert to mgC/m^-2 in the NTL LTER database. 
        pp_layer_daily_total_hw_time_corrected_m2 = pp_layer_daily_total_hw_time_corrected_m3 * layer_depth_interval 
        return pp_layer_daily_total_hw_time_corrected_m2  # mgC/m^2/day





    def get_phyto_pmax_at_depth(self, depth):
        '''
        @param depth: meters from surface
        @return:
        @rtype:
        '''
        validated_depth = self.validate_depth(depth)
        pmax = 0.0
        measurement = self.get_phytoplankton_photosynthesis_measurement_at_depth(validated_depth)
        if(measurement is not None):
            pmax = measurement.get_pmax()
        return pmax

    def get_phyto_alpha_at_depth(self, depth):
        '''
        @param depth: meters from surface
        @return:
        @rtype:
        '''
        validated_depth = self.validate_depth(depth)
        phyto_alpha = 0.0  # TODO: safer value?
        measurement = self.get_phytoplankton_photosynthesis_measurement_at_depth(validated_depth)
        if(measurement is not None):
            phyto_alpha = measurement.get_phyto_alpha()
        return phyto_alpha

    def get_phyto_beta_at_depth(self, depth):
        '''
        @param depth: meters from surface
        @return:
        @rtype:
        '''
        validated_depth = self.validate_depth(depth)
   
        phyto_beta = 0.0  # TODO: safer value?
        measurement = self.get_phytoplankton_photosynthesis_measurement_at_depth(validated_depth)
        if(measurement is not None):
            phyto_beta = measurement.get_phyto_beta()
            
        
            
        return phyto_beta



    def calculate_phytoplankton_primary_productivity(self, izt, depth, use_photoinhibition=True):
        '''
        Calculate Phytoplankton Primary Productivity
        @param izt: light at depth z, time t (umol*m^-2*s^-1)
        @param depth: depth (m)
        @return ppr_z (mg*m^-3*hr^-1)
        '''
        ppr_z = 0.0
        
        phyto_photo_measurement_z = self.get_phytoplankton_photosynthesis_measurement_at_depth(depth)
        if(phyto_photo_measurement_z is not None):


            phyto_pmax = self.get_phyto_pmax_at_depth(depth)  # mg C per m^3 per hour (mg*m^-3*hr^-1)
            phyto_alpha = self.get_phyto_alpha_at_depth(depth)  # (mg*m^-3*hr^-1)/(umol*m^-2*s^-1)
            phyto_beta = self.get_phyto_beta_at_depth(depth)  # (mg*m^-3*hr^-1)/(umol*m^-2*s^-1)

            if(use_photoinhibition):
                # P-I CURVE EQUATION WITH PHOTOINHIBITION  P = Pmax*(1-exp(-alpha*I/Pmax))*exp(-beta*I/Pmax)
                # P-I curve equation derived from Jassby/Platt, and specifically from http://web.pdx.edu/~rueterj/courses/esr473/notes/pvsi.htm
                # that website, of course, got it from "Photoinhibition of photosynthesis in natural assemblages of marine phytoplankton" By Platt, T., C.L. Gallegos and W.G. Harrison 1979.
                interim_value = 1 - mat.exp(-phyto_alpha * izt / phyto_pmax)  # [(mg*m^-3*hr^-1)/(umol*m^-2*s^-1) * (umol*m^-2*s^-1) = (mg*m^-3*hr^-1)
                other_interim_value = mat.exp(-phyto_beta * izt / phyto_pmax)  # (mg*m^-3*hr^-1), same as above
                ppr_z = phyto_pmax * interim_value * other_interim_value  # (mg*m^-3*hr^-1)

                
            else: 
                # P-I CURVE EQUATION WITH NO PHOTOINHIBITION. P = Pmax* tanh(alpha*I/Pmax)
                ppr_z = phyto_pmax * mat.tanh(phyto_alpha * izt / phyto_pmax) 
                

        return ppr_z  # (mg*m^-3*hr^-1)



    def get_phytoplankton_photosynthesis_measurement_at_depth(self, depth):
        '''
        @param depth:
        @return: shallowest layer measurement deeper than specified depth, or None if not found.
        @rtype:
        '''
        # find the shallowest layer_measurement that's deeper than this depth.
        # example: layers are at 5, 10, 15. Depth given is 5.5, then use measurement for second layer.
        measurement = None
        reverse_sorted_measurements = self.get_phyto_measurements_sorted_by_depth(True)  # sort reversed by depth.
        for layer_measurement in reverse_sorted_measurements:
            if (layer_measurement.get_depth() >= depth):                 
                measurement = layer_measurement
        return measurement


    def get_thermal_layer_depths(self):
        '''
        Sorts and returns the depths of the thermal layers. 
        @return: sorted list of thermal layer depths, from shallowest to deepest.
        @rtype: [] list 
        '''
        layer_depth_list = []
        reverse_sorted_measurements = self.get_phyto_measurements_sorted_by_depth(False)  # sort reversed by depth.
        for layer_measurement in reverse_sorted_measurements:
            layer_depth_list.append(layer_measurement.get_depth())
        return layer_depth_list
            

    def get_phyto_measurements_sorted_by_depth(self, reverse=False):
        '''
        Sort
        @return: sorted benthic measurements
        @rtype: list of BenthicPhotosynthesisMeasurement objects.
        '''
        # http://stackoverflow.com/questions/403421/how-to-sort-a-list-of-objects-in-python-based-on-an-attribute-of-the-objects
        thing = reverse
        unsorted_measurements = self.get_phytoplankton_photosynthesis_measurements()
        sorted_measurements = sorted(unsorted_measurements, key=lambda x: x.get_depth(), reverse=thing)
        return sorted_measurements


    ###########################################################
    # OTHER SCIENCE METHODS
    ###########################################################
    def check_if_depth_in_photic_zone(self, depth):
        '''
        Check If Depth In Photic Zone
        Used when adding photosynthesis measurements, calculating things, etc.
        @param depth: depth to check, in meters.
        @return: True if in photic zone, False if not.
        '''
        in_zone = True
        photic_zone_lower_bound = self.calculate_photic_zone_lower_bound()
        if(depth < 0 or depth > photic_zone_lower_bound):
            in_zone = False
        else:
            in_zone = True
        return in_zone


    def calculate_photic_zone_lower_bound(self):
        '''
        Calculate Photic Zone Lower Bound
        This is actually redundant. It can be accomplished just by calling calculate_depth_of_specific_light_percentage with PHOTIC_ZONE_LIGHT_PENETRATION_LEVEL_LOWER_BOUND.
        That said, I might one day wish to decouple photic zone lower bound from calculate_depth_of_specific_light_percentage, so I'm leaving this.
        NOTE: returns max depth if lower bound is deeper than max depth.
        @return: lower bound of the photic zone, in meters.
        @rtype: float
        '''
        lower_bound = self.calculate_depth_of_specific_light_percentage(self.PHOTIC_ZONE_LIGHT_PENETRATION_LEVEL_LOWER_BOUND)
        max_depth = self.get_max_depth()
        if(lower_bound > max_depth):
            lower_bound = max_depth
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
        depthOfSpecifiedLightProportion = 0.0  # the surface of the pond makes a good, safe default depth
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





    def calculate_light_at_depth_and_time(self, depth, time):
        '''
        Calculate Light At Depth And Time
        @param depth:
        @param time:
        @return: the light at that depth and time, in micromoles/m^2/sec
        @rtype: float
        '''

        validated_depth = self.validate_depth(depth)
        validated_time = self.validate_time(time)
        noonlight = self.get_noon_surface_light()
        length_of_day = self.get_length_of_day()
        surface_light_at_t = noonlight * np.sin(np.pi * validated_time / length_of_day)
        light_attenuation_coefficient = self.get_light_attenuation_coefficient()
        light_at_z_and_t = surface_light_at_t * np.exp(-light_attenuation_coefficient * validated_depth)
        return light_at_z_and_t



    def calculate_total_littoral_area(self):
        '''
        Calculate Total Littoral Area
        Uses kd to calculate the depth of 1% light, then uses the pond_shape to find sediment area above that.
        @return:
        @rtype:
        '''
        z1percent = self.calculate_photic_zone_lower_bound()
        shape_of_pond = self.get_pond_shape()

        littoral_area = shape_of_pond.get_sediment_area_above_depth(z1percent, Pond.DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS)
        return littoral_area

    def calculate_total_photic_volume(self):
        z1percent = self.calculate_photic_zone_lower_bound()
        shape_of_pond = self.get_pond_shape()

        photic_volume = shape_of_pond.get_volume_above_depth(z1percent, Pond.DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS)
        return photic_volume


    def interpolate_values_at_depth(self, depth, depths_list=[], values_list=[]):
        '''
        INTERPOLATE VALUES AT DEPTH
        Essentially, given an array of "x" (validated_depths) and "y" values, interpolates "y" value at specified validated_depth.

        Based on SciPy interpolation:http://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html

        Used for things like, "I have pmax values at 0 and 1, but I need one at 0.5)

        @param depth: depth to interpolate _at_. In the above example, this would be 0.5
        @param depths_list: list of depths where we have data.
        @param values_list: corresponding data that goes with the depths. So value[0] is the value at depth[0] for example.
        @return: a single value, the value calculated for the specified depth.
        @rtype: a number. #TODO: what _kind_ of number?
        '''


        # Uses http://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html
        validated_depth = self.validate_depth(depth)

        max_depth_given = max(depths_list)
        min_depth_given = min(depths_list)

        if(validated_depth > max_depth_given):
            validated_depth = max_depth_given
        elif(min_depth_given < min_depth_given):
            validated_depth = min_depth_given


        # get interpolation function #TODO: x, y need to be in order for scipy.interp1d to work I think. Check?
        x = depths_list
        y = values_list

        if(len(x)<2):
            traceback.print_exc()
            error_message = 'Cannot interpolate at depth ', depth,', because there are not enough data points!'
            error_message = str(error_message)
            print error_message
            raise Exception(error_message)      
        f = interp1d(x, y)

        # magic from http://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html
        #SPLINES....!!!
#         tck = interpolate.splrep(x, y, s=0)
#         xnew = [validated_depth]
#         spline_interpolated = interpolate.splev(xnew, tck, der=0) #0th derivative
        linear_interpolated = f(validated_depth)




#         value_at_depth = spline_interpolated[0] #TODO: inefficient to get the whole array and return just one.
        value_at_depth = linear_interpolated
        return value_at_depth






    def calculate_depths_of_specific_light_percentages(self, light_penetration_depths):
        '''
        CALCULATE DEPTHS OF SPECIFIC LIGHT PERCENTAGES
        Given a list of light penetration depths returns the depth in meters needed for each of those light penetration levels.
        I only used this once, for making some testing data.
        @rtype: list
        '''
        depths = []
        for light_penetration_depth in light_penetration_depths:
            depth_m_of_light_penetration = self.calculate_depth_of_specific_light_percentage(light_penetration_depth)
            depths.append(depth_m_of_light_penetration)
        return depths
    



        


############################################################################
# TESTING SECTION
###########################################################################


def main():
    '''
    TESTING TIME!!!

    '''
    print "Hello, world. You should never see this. I deleted all the test code that was here anyway."




if __name__ == "__main__":
    main()
