'''
Created on Jun 18, 2015

@author: cdleong
'''
from pond_shape import PondShape
from scipy.interpolate import interp1d


class BathymetricPondShape(PondShape):
    '''
    This class stores information about the shape of a pond based on bathymetric measurements.
    In essence, this means that the area of the pond is given at various depths.
    Example: "At depth of 10 meters, water surface area is 6,000 square meters."
    
    For depths without a specified area, the class will interpolate using scipy.interpolate.interp1d, 
    documented at http://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp1d.html#scipy.interpolate.interp1d
    
    It will not work well if not given at least the area at the surface and at the bottom of the lake. 
    '''
    
    #CONSTANTS
    DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS = 0.1  # ten centimeters, 0.1 meters. Arbitrary.
    

    # dict tutorial here: http://www.tutorialspoint.com/python/python_dictionary.htm
    water_surface_areas = {}  #Dictionary. Keys are depth values in meters, values are the surface area at that depth.
    #June 22 edit: depth intervals are now independent for every calculcation.


    def __init__(self, areas={}):
        '''
        Constructor
        @param areas: a python dict containing depth/area pairs.
        '''
        self.water_surface_areas = areas





    def get_dict(self):
        '''
        Getter method.
        @return: the dictionary of depth/area pairs.
        @rtype: python dict.
        '''
        return self.water_surface_areas

    def get_volume(self):
        '''
        Get Total Lake Volume
        @return:  the total volume of the entire lake, in cubic meters
        @rtype: float
        '''
        return self.get_volume_above_depth(self.get_max_depth())

    def addBathymetryLayer(self, depth_value=0.0, area_value=0.0):
        '''
        Adds a depth/area pair to the dictionary. 
        @param depth_value: float value, depth_value in meters of area_value measurement.
        @param area_value:  float value, area_value in meters squared at depth_value.
        '''
        if (depth_value < 0.0 or area_value <= 0.0):
            raise Exception("invalid depth_value or area_value. Depth value must NOT be less than zero. Depth Value given: ",depth_value, " Area must NOT be less than, or equal to, zero. area_value given:",area_value)
        else:
            self.water_surface_areas[depth_value]=area_value



    def update_shape(self, other_pond_shape):
        '''
        Adds all depth/area pairs from other_pond_shape to this one.        
        '''
        #TODO: validate other data.
        #TODO: handle exceptions/problems.
        otherdict = other_pond_shape.water_surface_areas
        self.water_surface_areas.update(otherdict)

    def get_max_depth(self):
        '''
        Get Maximum Depth
        finds the maximum depth in the dict of areas.
        
        Throws exception if dictionary is empty.
        
        @return: in meters, the maximum depth of the lake.
        @rtype: float
        '''
        max_depth =0.0
        keys = self.water_surface_areas.keys()        
        has_areas = bool(self.water_surface_areas)
        
        if(False == has_areas):
            raise Exception("No shape data exists. max depth is 0")
        else:
            max_depth = max(keys)
        return max_depth


    def get_mean_depth(self, depth_interval=DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS):
        '''
        Get Mean Depth
        @return: average depth, in meters, for the whole pond.
        @rtype: float
        '''
        validated_depth_interval = self.validate_depth_interval(depth_interval)
        max_depth = self.get_max_depth()
        total_area = self.get_sediment_area_above_depth(max_depth)
        if(0==total_area):
            #only possible if the sides are literally vertical.
            return max_depth


        current_depth = validated_depth_interval  # no point starting at 0, since that's just gonna be zero anyway.
        weighted_total = 0.0 #initialize to float
        while current_depth <= max_depth:
            area_at_depth = self.get_sediment_surface_area_at_depth(current_depth) # there are this many square meters at this depth
            weighted_total+=area_at_depth*current_depth
            current_depth += validated_depth_interval

        mean_depth  = weighted_total/total_area
        return mean_depth




    def get_water_surface_area_at_depth(self, depth=0.0):
        '''
        Get Water Surface Area at Specified Depth
        Figures out the surface area at depth

        Uses http://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html
        For area/depth combinations not given.
        @param depth: depth in meters to calculate at. depth should between 0 and max_depth. It'll be set to one of those if not so.
        @rtype: float
        '''
        #TODO: errors if given stuff outside proper range.
        
        validated_depth = self.validate_depth(depth)
        

        # get interpolation function
        x = self.water_surface_areas.keys()
        y = self.water_surface_areas.values()        
        if(len(x)<2):
            error_message = "Cannot interpolate to determine water surface area at depth ", depth,", because there are not enough depth/area pairs."
            print error_message
            raise Exception(str(error_message))
        
        f = interp1d(x, y)
        
        #interpolate
        
        water_surface_area_at_depth = f(validated_depth)


        return water_surface_area_at_depth








    def get_sediment_surface_area_at_depth(self, depth=0.0, depth_interval=None):
        '''
        Get Sediment Surface Area at Specified Depth
        Essentially, returns an estimate of the area of the section of lake bottom,
        whose bottom edge is at depth and top edge is at (depth-validated_depth_interval)
        On a perfectly conical lake this would form a truncated inverted cone with a hole in the middle.
        If given depth = max_depth and validated_depth_interval also = max_depth, should estimate sediment for the whole lake.
        ...which should add up to water surface area at depth 0 by the way

        @param depth: depth in meters to calculate at. depth should between 0 and max_depth. It'll be set to one of those if not so.
        @param depth_interval:
        @return: sediment area
        @rtype: float
        '''
        if(depth_interval is None):
            depth_interval = 1 #1 meter by default

        validated_depth = self.validate_depth(depth)
        validated_depth_interval = self.validate_depth_interval(depth_interval)
#         validated_depth_interval = self.get_depth_interval_meters()
        lower_edge_depth = validated_depth
        upper_edge_depth = self.validate_depth(validated_depth - validated_depth_interval)


        #validate the depths of the two
        if(lower_edge_depth > upper_edge_depth):  # upper edge should be a smaller value of depth
            # all is well. Do nothing.
            pass
        elif (lower_edge_depth < upper_edge_depth):
            # validated_depth_interval was negative?
            # switch them.
            lower_edge_depth, upper_edge_depth = upper_edge_depth, lower_edge_depth
        else:  # they are the same
            #lower and upper bounds of sediment region are the same. Area is 0
            return 0


        upper_water_area = self.get_water_surface_area_at_depth(upper_edge_depth)
        lower_water_area = self.get_water_surface_area_at_depth(lower_edge_depth)


        # The theory is, we get basically the top side of a right cone/donut thing.
        #
        # ASCII picture of a lake cross-section:
        #
        #          "sediment_surface_area"
        #          |
        #  ________|__________
        #  |                  |
        #  \/                 \/
        # ________________________     <--- upper_water_area
        # \   |              |   /
        #  \  |depth_interval|  /
        # h \ |              | /
        #    \|______________|/        <--- lower_water_area
        #
        # What we ACTUALLY want is h, but in practice the slope is generally shallow enough in the littoral zone
        # (the zone we are interested in) that this is a good approximation. Source: Dr. Vadeboncoeur
        sediment_surface_area = upper_water_area - lower_water_area

        # it's _possible_, technically, that the lake gets *wider* as it goes down. Is it?
        sediment_surface_area = abs(sediment_surface_area)

#         print "calculating sediment surface area, upper_water_area is ", upper_water_area, " lower_water_area is ", lower_water_area

        return sediment_surface_area




    def get_volume_above_depth(self, depth=0.0, depth_interval=DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS):
        '''
        Get Volume Above Depth
        O(number of depth intervals*O(get_volume_at_depth()))
        @param depth: depth in meters to calculate at. depth should between 0 and max_depth. It'll be set to one of those if not so.
        @return: volume in cubic meters
        @rtype: float

        '''

        validated_depth = self.validate_depth(depth)
        validated_depth_interval = self.validate_depth_interval(depth_interval)

        # just find the volume at each interval and add them all up.


        current_depth = 0.0  # no point starting at 0, since that's just gonna be zero anyway.
        total_volume = 0.0
        while current_depth <= validated_depth:
            current_volume = self.get_volume_at_depth(current_depth, validated_depth_interval)
            total_volume += current_volume
            current_depth += validated_depth_interval
        return total_volume


    def get_volume_at_depth(self, depth=0.0, depth_interval = DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS):
        '''
        Given a depth, gives the volume of the shape with a lower surface at area and upper surface at area-validated_depth_interval
        @param depth: depth in meters to calculate at. depth should between 0 and max_depth. It'll be set to one of those if not so.
        @return: volume.
        @rtype: float
        '''
        ####################################################
        # ASCII picture of an example lake cross-section:
        #
        # ________________________     <-areas[z0]
        # .\   |              |   /.
        # . \  |interval      |  / .
        # .  \ |              | /  .
        # ....\|______________|/....    <-areas[z1]
        #                        ^
        #                        |
        #                        |
        #                        x = 1/2 (areas[z0]-areas[z1])
        #
        # error is just 2x*interval, or just (areas[z0]-areas[z1])*interval
        # Volume from z0 to z1 can be approximated using
        # areas[z0]*interval, which overestimates by error    :result is correctAnswer+error
        # areas[z1]*interval, which underestimates by error   :result is correctAnswer-error
        # correct answer should be areas[z0]*interval -error or areas[z1]*interval +error
        #
        ####################################################

        validated_depth = self.validate_depth(depth)
        validated_depth_interval = self.validate_depth_interval(depth_interval)
        lower_edge_depth = validated_depth
        upper_edge_depth = self.validate_depth(validated_depth - validated_depth_interval)


        #validate the depths of the two
        if(lower_edge_depth > upper_edge_depth):  # upper edge should be a smaller value of depth
            # all is well. Do nothing.
            pass
        elif (lower_edge_depth < upper_edge_depth):
            # validated_depth_interval was negative?
            lower_edge_depth, upper_edge_depth = upper_edge_depth, lower_edge_depth   # switch them.
        else:  
            # they are the same
            return 0.0

        upper_water_area = self.get_water_surface_area_at_depth(upper_edge_depth)
        lower_water_area = self.get_water_surface_area_at_depth(lower_edge_depth)

        upper_calculated_volume = upper_water_area*validated_depth_interval #equivalent to correct answer + error
        lower_calculated_volume = lower_water_area*validated_depth_interval #equivalent to correct answer - error


        volume_at_depth = (upper_calculated_volume+lower_calculated_volume)/2 #equivalent to (correct answer)
        return volume_at_depth

    def get_sediment_area_above_depth(self, depth=0.0, depth_interval=DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS):
        '''
        Get Sediment Area above depth
        @param depth: depth in meters to calculate at. depth should between 0 and max_depth. It'll be set to one of those if not so.
        @return: the area of the sediment above a specific depth.
        @rtype: float value
        '''


        validated_depth = self.validate_depth(depth)
        validated_depth_interval = self.validate_depth_interval(depth_interval)

        # add up the sediment area at every interval.
        total_area = 0.0

        current_depth = 0.0
        while current_depth <= validated_depth:
            current_area = self.get_sediment_surface_area_at_depth(current_depth, validated_depth_interval)
            total_area += current_area
            current_depth += validated_depth_interval
#             print "Calculating sediment area above depth",validated_depth ,"current depth: ", current_depth, ". sediment area with interval ", validated_depth_interval , " is ", current_area

        return total_area

    def get_fractional_sediment_area_at_depth(self, depth=0.0, total_sediment_area=None, depth_interval =DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS):
        '''
        Sediment area at depth, as a fraction of total_sediment_area.
        If total area isn't supplied, we go with total littoral area.

        For this to work with littoral area, pond object needs to supply it with the proper littoral area, which must be calculated using the light attenuation coefficient.
        @param depth:
        @param total_sediment area:
        @param depth_interval:
        @return:
        @rtype:
        '''
        if(total_sediment_area is None):
            total_sediment_area = self.get_sediment_area_above_depth(self.get_max_depth())



        validated_depth = self.validate_depth(depth)
        sediment_area_at_depth = self.get_sediment_surface_area_at_depth(validated_depth, depth_interval)
        fractional_sediment_area = sediment_area_at_depth/total_sediment_area
        return fractional_sediment_area


    def validate_depth(self, depth):
        '''
        Given a depth, checks to see if it is between 0 and max_depth.
        If outside that range, sets it to the closest one.
        @param depth: the value to be validated.
        @return: a float value between 0 and max depth of pond
        '''

        validated_depth = 0.0
        if(depth < 0):
            validated_depth=0.0
        elif(depth > self.get_max_depth()):
            validated_depth = self.get_max_depth()
        else:
            validated_depth=depth

        return validated_depth

    def validate_depth_interval(self, depth_interval):
        '''
        Checks to make sure that the depth_interval is between 0 and self.get_max_depth() meters. If value is less than 0, it sets it to 1% of maximum depth
        @param depth_interval:depth to validate, in meters.
        @return: a value between 0 and the maximum depth of the lake.
        @rtype: float
        '''
        max_depth= self.get_max_depth()
        validated_depth_interval = self.DEFAULT_DEPTH_INTERVAL_FOR_CALCULATIONS #default value, chosen based on 
        if(depth_interval<=0):
            validated_depth_interval=max_depth/100 #set to 1% of max depth. Seems safe enough.
        elif(depth_interval>max_depth):
            validated_depth_interval=max_depth
        else:
            validated_depth_interval = depth_interval
        return validated_depth_interval

    def add_bathymetry(self, otherObject):
        '''
        Given another Bathymetric Pond Shape, copies all entries in the other's dictionary of depth/area pairs into the dictionary of this one.
        @param otherObject:
        '''
        if(isinstance(otherObject, BathymetricPondShape)):
            thisDict = self.water_surface_areas
            otherdict = otherObject.water_surface_areas
            thisDict.update(otherdict)
            self.water_surface_areas=thisDict

def main():
    '''
    Used for testing!
    '''
    
    print "hello world"
#     areas = {0:100, 0.25:75,5:50, 10:1}
    areas = {0:640000, 1:600960,2:565120,3:536960,4:516480,5:492800,6:467840,7:442880,8:421120,9:404480,10:374400,11:345600,12:318720,13:293120,14:268800,15:243200,16:190720,17:130560,18:74240,19:33280,20:0}
    littoral_area = 5814043.69309
    shape_instance = BathymetricPondShape(areas)
    print "max depth is (should be 10): ", shape_instance.get_max_depth()
    print "depths ", shape_instance.water_surface_areas.keys()
    print "areas ", shape_instance.water_surface_areas.values()

    max_depth = shape_instance.get_max_depth()
    half_max_depth = max_depth / 2

#     print "sediment area total above depth ", max_depth, " is ", shape_instance.get_sediment_area_above_depth(max_depth)
#     print "sediment area total above depth ", half_max_depth, " is ", shape_instance.get_sediment_area_above_depth(half_max_depth)
#
#     print "total volume is", shape_instance.get_volume()
#     print "total volume above depth ", max_depth, " is ", shape_instance.get_volume_above_depth(max_depth)
#     print "total volume above depth ", half_max_depth, " is ", shape_instance.get_volume_above_depth(half_max_depth)
#
#     print "mean depth is ", shape_instance.get_mean_depth()

    #testing volume calculations:
    vol_depth = 1
    depth_interval = 1
    print "volume at depth ",vol_depth," with dz = ", depth_interval, " is ", shape_instance.get_volume_at_depth(vol_depth, depth_interval)
    print "volume above depth ",vol_depth," with dz = ", depth_interval, " is ", shape_instance.get_volume_above_depth(vol_depth, depth_interval)


    depth = 0.0
    total_fraction = 0.0
    while (depth<=shape_instance.get_max_depth()):
#         print "water surface area at depth ", depth, " is ", shape_instance.get_water_surface_area_at_depth(depth)
#         print "sediment surface area at depth ", depth, " with interval (in meters) of ", 1, " is: ", shape_instance.get_sediment_surface_area_at_depth(depth,1)
        f_area = shape_instance.get_fractional_sediment_area_at_depth(depth, littoral_area)
#         print "fractional sediment area is ", f_area
#         print "current total fraction is ", total_fraction
        depth+=1
        total_fraction+=f_area
#     print "total fraction should add to 1, and is: ", total_fraction




if __name__ == "__main__":
    main()

