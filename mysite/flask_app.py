import os

import traceback
from flask import Flask, request, url_for, render_template, redirect, Response, session


import StringIO




from data_reader import DataReader

#used for the excel output.
import xlwt #excel writing
import mimetypes
from werkzeug.datastructures import Headers #used for exporting files?
import jsonpickle

##############################################################
#IMPORTANT VARIABLES
#
##############################################################

#How to work with file uploads http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# This is the path to the upload directory


ALLOWED_EXTENSIONS = set(['xls', 'xlsx', 'csv'])
TEMPLATE_FILE = 'template.xls'
TEMPLATE_FILE_ROUTE = '/'+TEMPLATE_FILE
EXAMPLE_FILE = 'example_data.xls'
EXAMPLE_FILE_ROUTE = '/'+EXAMPLE_FILE
INTERNAL_SERVER_ERROR_TEMPLATE_FILE = "500.html"
INTERNAL_SERVER_ERROR_TEMPLATE_ROUTE = '/'+INTERNAL_SERVER_ERROR_TEMPLATE_FILE

FIRST_DATA_ROW_FOR_EXPORT = 1


# Initialize the Flask application
app = Flask(__name__)

random_number = os.urandom(24)
app.secret_key = random_number

# These are the extension that we are accepting to be uploaded
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #arbitrary 16 megabyte upload limit













# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
           
           

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def indexView():
    '''
    Renders the template for the index.
    '''
    
    #http://runnable.com/UiPcaBXaxGNYAAAL/how-to-upload-a-uploaded_file-to-the-server-in-flask-for-python
    if request.method == 'POST': #true if the button "upload" is clicked
        # Get the name of the uploaded uploaded_file
        uploaded_file = request.files['uploaded_file']
        

        
        
        
        print type(uploaded_file)
        # Check if the uploaded_file is one of the allowed types/extensions
        if uploaded_file and allowed_file(uploaded_file.filename):
            
            
            
            pond_file = request.files['uploaded_file']

            try:                   
                reader = DataReader("") #I don't plan on using this filename, thanks
                pondList = reader.readFile(pond_file.read()) #read method is http://werkzeug.pocoo.org/docs/0.10/datastructures/#werkzeug.datastructures.FileStorage,                 
            except Exception as e:
                print "error in getPondList"
                print str(e)
                return render_template(INTERNAL_SERVER_ERROR_TEMPLATE_ROUTE, error = str(e))
            
            number_of_ponds = len(pondList)
            pond_year_list = []
            pond_id_list = []
            pond_day_list = []
            pond_bppr_list = []
            pond_pppr_list = []
            for pond in pondList:
                pond_year_list.append(pond.get_year())
                pond_id_list.append(pond.get_lake_id())
                pond_day_list.append(pond.get_day_of_year())
                pond_bppr_list.append(pond.calculate_daily_whole_lake_benthic_primary_production_m2())
                pond_pppr_list.append(pond.calculate_daily_whole_lake_phytoplankton_primary_production_m2())
                
            
            
            
            #add things to session dict, so as to pass them to other views
            
            session['number_of_ponds'] = number_of_ponds
            session['pond_year_list'] = pond_year_list
            session['pond_id_list'] = pond_id_list
            session['pond_day_list'] = pond_day_list
            session['pond_bppr_list'] = pond_bppr_list
            session['pond_pppr_list'] = pond_pppr_list
            

            
            ##################################################################
            #let's try something. AARDVARK <--easy to search for this
            #(this might be more work than making Pond objects serializable)
            ##################################################################
            ##trying http://jsonpickle.github.io/
            pickled_ponds_list = []
            for pond in pondList:
                pickled_pond = jsonpickle.encode(pond)
                pickled_ponds_list.append(pickled_pond)
                
            session['pickled_ponds_list'] = pickled_ponds_list            
            




            return redirect(url_for("primary_production"))

        else:
            error_message = "Apologies, that file extension is not allowed. Please try one of the allowed extensions."
            return render_template('home_with_error.html', template_file_route = TEMPLATE_FILE_ROUTE, example_file_route = EXAMPLE_FILE_ROUTE,error_message=error_message)

    return render_template('home.html', template_file_route = TEMPLATE_FILE_ROUTE, example_file_route = EXAMPLE_FILE_ROUTE)




@app.route(TEMPLATE_FILE_ROUTE, methods=['GET', 'POST'])
def template():
    '''
    Used to offer template data file
    #http://stackoverflow.com/questions/20646822/how-to-serve-static-files-in-flask    
    '''
    try:
        return app.send_static_file(TEMPLATE_FILE)
    except Exception as e:
        print str(e)
        return render_template(INTERNAL_SERVER_ERROR_TEMPLATE_ROUTE, error = str(e))



@app.route(EXAMPLE_FILE_ROUTE, methods=['GET', 'POST'])
def example_file_view():
    '''
    Used to offer example data file
    #http://stackoverflow.com/questions/20646822/how-to-serve-static-files-in-flask
    '''
    try:
        return app.send_static_file(EXAMPLE_FILE)
    except Exception as e:
        print str(e)
        return render_template(INTERNAL_SERVER_ERROR_TEMPLATE_ROUTE, error = str(e))

################################################################
#renders the primary_production template.
################################################################
@app.route('/primary_production', methods=['GET', 'POST'])
@app.route('/primary_production.html', methods=['GET', 'POST'])
def primary_production():
    '''
    Renders the primary_production template, which shows calculated values and a button to download them.
    '''
    try:
        return render_template("primary_production.html")
    except Exception as e:
        print str(e)
        return render_template(INTERNAL_SERVER_ERROR_TEMPLATE_ROUTE, error = str(e))




@app.route('/export')
def export_view():
    '''
    Code to make an excel file for download.
    Modified from...
    http://snipplr.com/view/69344/create-excel-file-with-xlwt-and-insert-in-flask-response-valid-for-jqueryfiledownload/    
    '''
    #########################
    # Code for creating Flask
    # response
    #########################
    response = Response()
    response.status_code = 200


    ##################################
    # Code for creating Excel data and
    # inserting into Flask response
    ##################################

    #.... code here for adding worksheets and cells
    #Create a new workbook object
    workbook = xlwt.Workbook()

    #Add a sheet
    daily_worksheet = workbook.add_sheet('Daily Statistics')
    
    #columns to write to
    year_column = 0
    lake_ID_column = year_column+1
    day_of_year_column = lake_ID_column+1
    bppr_column = day_of_year_column+1
    pppr_column = bppr_column+1        
        
    #get data from session, write to daily_worksheet
    year_list = session['pond_year_list']
    lake_id_list = session['pond_id_list']
    day_of_year_list = session['pond_day_list']
    bpprList = session['pond_bppr_list']
    ppprList = session['pond_pppr_list']

    write_column_to_worksheet(daily_worksheet, year_column, "year", year_list)
    write_column_to_worksheet(daily_worksheet, lake_ID_column, "Lake ID", lake_id_list)
    write_column_to_worksheet(daily_worksheet, day_of_year_column, "day of year", day_of_year_list)
    write_column_to_worksheet(daily_worksheet, bppr_column, "BPPR", bpprList)
    write_column_to_worksheet(daily_worksheet, pppr_column, "PPPR", ppprList)

    
    #Add another sheet
    hourly_worksheet = workbook.add_sheet('Hourly Statistics')
    
    #PLATYPUS
    pickled_ponds_list = session['pickled_ponds_list']
    pond_list = []
    for pickled_pond in pickled_ponds_list:
        pond = jsonpickle.decode(pickled_pond)
        pond_list.append(pond)
    print "******************************************************"
    print "pickled ponds list: ", pickled_ponds_list
    print "unpickled ponds list: ", pond_list
    for pond in pond_list:
        print "pond id is, ", pond.get_lake_id()
    print "******************************************************"
    
    #columns to write to
    hour_column = 0
   
        
    #get data from session, write to daily_worksheet
    hour_list = [0,0.5,1.0]


    write_column_to_worksheet(hourly_worksheet, hour_column, "hour", hour_list)


    #This is the magic. The workbook is saved into the StringIO object,
    #then that is passed to response for Flask to use.
    output = StringIO.StringIO()
    workbook.save(output)
    response.data = output.getvalue()

    ################################
    # Code for setting correct
    # headers for jquery.fileDownload
    #################################
    filename = "export.xls"
    mimetype_tuple = mimetypes.guess_type(filename)

    #HTTP headers for forcing file download
    response_headers = Headers({
            'Pragma': "public",  # required,
            'Expires': '0',
            'Cache-Control': 'must-revalidate, post-check=0, pre-check=0',
            'Cache-Control': 'private',  # required for certain browsers,
            'Content-Type': mimetype_tuple[0],
            'Content-Disposition': 'attachment; filename=\"%s\";' % filename,
            'Content-Transfer-Encoding': 'binary',
            'Content-Length': len(response.data)
        })

    if not mimetype_tuple[1] is None:
        response.update({
                'Content-Encoding': mimetype_tuple[1]
            })

    response.headers = response_headers

    #as per jquery.fileDownload.js requirements
    response.set_cookie('fileDownload', 'true', path='/')

    ################################
    # Return the response
    #################################
    return response

def write_column_to_worksheet(worksheet,column_number=0, column_header = "", values_list=[]):
    '''
    Prepends a column header and puts the data in values_list into worksheet at the specified column
    @param worksheet: An xlrd worksheet to write to.
    @param column_number: Column number to write to.
    @param column_header: Header to put at the top of the column.
    @param values_list: list of values to put in the column.
    '''
    print "writing column to worksheet"
    values_list.insert(0, column_header) #stick the column header at the front.
    numRows = len(values_list)


    for i in range(0, numRows):
        row = i
        column = column_number
        value=values_list[row]
        worksheet.write(row,column,value)


@app.errorhandler(413)
def request_entity_too_large(error):
    '''
    Error handler view. Should display when files that are too large are uploaded.
    '''
    return 'File Too Large'

@app.errorhandler(404)
def pageNotFound(error):
    
    return "Page not found"

@app.errorhandler(500)
def internalServerError(internal_exception):
    '''
    Prints internal program exceptions so they are visible by the user. Stopgap measure for usability.
    
    '''
    
    #TODO: more and better errors, so that when specific parts of the data are wrong, users can figure it out.
    traceback.print_exc()
    print str(internal_exception)
    return render_template(INTERNAL_SERVER_ERROR_TEMPLATE_ROUTE, error = str(internal_exception))





if __name__ == '__main__':

    print "a random number is: ", random_number
    
    
    print "secret key is", app.secret_key
    debug_mode = False
    i_am_sure_i_want_to_let_people_execute_arbitrary_code = "no" #"yes" for yes.
    i_want_an_externally_visible_site = False
    if(debug_mode and "yes"==i_am_sure_i_want_to_let_people_execute_arbitrary_code):
        print "running in debug mode"
        app.run(debug=True)
        print "stopped running app"
    elif(i_want_an_externally_visible_site):
        app.run(host='0.0.0.0')
    else:
        app.run()