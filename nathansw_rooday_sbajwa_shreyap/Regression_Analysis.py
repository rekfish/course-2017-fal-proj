import json
from urllib.request import urlopen
import time
import pprint 
import datetime
import dml
import prov.model
import uuid
from bson import ObjectId
import pandas as pd
import numpy as np
import seaborn
from sklearn.model_selection import cross_val_predict
from sklearn import linear_model
from sklearn import metrics
import sklearn
import statsmodels.api as sm
import statsmodels

### Algorithm 1

class Regression_Analysis(dml.Algorithm):

  contributor = 'nathansw_rooday_sbajwa_shreyap'
  ### Make sure this is the correct dataset file name
  reads = ['nathansw_rooday_sbajwa_shreyap.otpByLine', 'nathansw_rooday_sbajwa_shreyap.stops', 'nathansw_rooday_sbajwa_shreyap.stopsVsLines']
    
  # Currently it just creates a csv file 
  writes = ['nathansw_rooday_sbajwa_shreyap.regressionAnalysis']

  @staticmethod
  def execute(trial=False):
    startTime = datetime.datetime.now()
    client = dml.pymongo.MongoClient()
    repo = client.repo
    repo.authenticate('nathansw_rooday_sbajwa_shreyap', 'nathansw_rooday_sbajwa_shreyap')

    # Read data from mongo
    mbta_db = repo['nathansw_rooday_sbajwa_shreyap.otpByLine']
    stops_db = repo['nathansw_rooday_sbajwa_shreyap.stops']
    stopsVsLines_db = repo['nathansw_rooday_sbajwa_shreyap.stopsVsLines']

    # Read data into pandas
    otpData = mbta_db.find_one()
    del otpData['_id']
    otp_by_line = pd.DataFrame.from_dict(otpData)
    otp_by_line = otp_by_line.transpose()
    otp_by_line[otp_by_line['Peak Service']==''] = np.nan
    otp_by_line[otp_by_line['Off-Peak Service']==''] = np.nan

    stopsData = stops_db.find_one()
    del stopsData['_id']
    stops = pd.DataFrame.from_dict(stopsData)

    stop_by_line_data = stopsVsLines_db.find_one()
    del stop_by_line_data['_id']
    stop_by_line = pd.DataFrame([(key, x) for key,val in stop_by_line_data.items() for x in val], columns=['Name', 'Values'])
    stop_by_line.columns = ['Route','Stop']
    stop_by_line  = stop_by_line.set_index('Stop')
    
    stop_route_neighborhood = stop_by_line.join(stops.set_index('stop_id'),how='left')
    stop_route_neighborhood = stop_route_neighborhood[stop_route_neighborhood['neighborhood'].notnull()]
    stop_route_neighborhood['stop_id'] = stop_route_neighborhood.index
    merged = pd.merge(otp_by_line,stop_route_neighborhood, left_index = True, right_on='Route',how='right')
    merged_stop = merged[merged['Peak Service'].notnull()]
    
    stop_dummy_city = pd.get_dummies(merged_stop['city'])
    stop_dummy_neighborhood = pd.get_dummies(merged_stop['neighborhood'])
    merged_dummy_city = merged_stop.join(stop_dummy_city)
    merged_dummy_city_final = merged_dummy_city.groupby('Route').max()
    x_cols = merged_dummy_city_final.columns[8:]
    y_cols = 'Off-Peak Service'
    model = sm.GLM(merged_dummy_city_final[y_cols],merged_dummy_city_final[x_cols], family=sm.families.Gaussian())
    results = model.fit()
    resultsKeys = results.params.keys()

    coefficients = {}
    for key in resultsKeys:
      coefficients[key] = results.params[key]

    repo.dropCollection('regressionAnalysis')
    repo.createCollection('regressionAnalysis')
    repo['nathansw_rooday_sbajwa_shreyap.regressionAnalysis'].insert_one(coefficients)
    
    repo.logout()
    endTime = datetime.datetime.now()
    return {"start":startTime, "end":endTime}
    

  @staticmethod
  def provenance(doc = prov.model.ProvDocument(), startTime=None, endTime=None):
    client = dml.pymongo.MongoClient()
    repo = client.repo

    ##########################################################

    ## Namespaces
    doc.add_namespace('alg', 'http://datamechanics.io/algorithm/sbajwa_nathansw/') # The scripts in / format.
    doc.add_namespace('dat', 'http://datamechanics.io/data/sbajwa_nathansw/') # The data sets in / format.
    doc.add_namespace('ont', 'http://datamechanics.io/ontology#')
    doc.add_namespace('log', 'http://datamechanics.io/log#') # The event log.


    """
    ## Agents
    this_script = doc.agent('alg:nathansw_rooday_sbajwa_shreyap#mbta_stops_lines', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})

    ## Activities
    get_mbta_stops_lines = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)

    ## Entitites
    # Data Source
    resource = 
    # Data Generated
    mbta_stops_lines = 
       
    ############################################################

        ## wasAssociatedWith      

    ## used   

    ## wasGeneratedBy

    ## wasAttributedTo    

    ## wasDerivedFrom

    ############################################################
    """
    repo.logout()

    return doc

Regression_Analysis.execute()