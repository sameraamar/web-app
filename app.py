#import os
from flask import Flask, flash, redirect, render_template, request, url_for, jsonify
from flask_pymongo import PyMongo
import time



app = Flask(__name__)

app.config['MONGO_HOST'] = 'localhost'
app.config['MONGO_PORT'] = 27017

app.config['MONGO_DBNAME'] = 'events2012'
app.config['TEMPLATES_AUTO_RELOAD'] = True
collname = 'posts'

app.secret_key = 'some_secret'

mongo = PyMongo(app)

values = []

#db = mongo[dbname]
#coll = mongo.db[collname]

#client = MongoClient(host, int(port))
#db = client[dbname]
#dbcoll = db[collname]

#from models import Result


#lsh_param =  [
#               {'name' : 'k', 'default' : 10, 'label' : 'Hyperplane', } ,
#               {'name' : 'maxB', 'default' : 500, 'label' : 'Max bucket size', 'placeholder' : ''} ,
#               {'name' : 'tables', 'default' : 64, 'label' : 'Number of Hashtables', 'placeholder' : ''} ,
#               {'name' : 'maxB', 'default' : 500, 'label' : 'Max bucket size', 'placeholder' : ''} 
#             ]
#
#
#thread_param = [             
#               {'name' : 'max_threads', 'default' : 2000, 'label' : 'Max Threads', 'placeholder' : ''} ,
#               {'name' : 'max_docs', 'default' : 10, 'label' : 'Max Input Documents', 'placeholder' : ''} ,
#               {'name' : 'threshold', 'default' : 0.5, 'label' : 'Threashold', 'placeholder' : ''} 
#               ]
#db_param = [
#               {'name' : 'dbhost', 'default' : 'localhost', 'label' : 'Mongo DB Host', 'placeholder' : ''} ,
#               {'name' : 'dbport', 'default' : 27017, 'label' : 'Mongo DB Port', 'placeholder' : ''} ,
#               {'name' : 'dbname', 'default' : 'events2012', 'label' : 'MongoDB-DB Name', 'placeholder' : ''} ,
#               {'name' : 'dbcoll', 'default' : 'posts', 'label' : 'MongoDB-Collection', 'placeholder' : ''} 
#            ]
#
#
#parameters = {
#              'LSH Parameters' : lsh_param
#              ,
#              'Thread Parameters': thread_param 
#              ,
#              'Connection Details': db_param
#             }
#               #{'name' : 'page', 'default' : 0, 'label' : 'Page', 'placeholder' : ''} 
             


lsh = {
          'title' : 'LSH parameters',
          'k' :         { 'value' : 13, 'label' : 'Hyperplanes' } ,
          'maxB' :      { 'value' : 500, 'label' : 'Max bucket size' } ,
          'tables' :    { 'value' : 64, 'label' : 'Number of Hashtables' } 
      }

thread = {
          'title' : 'Thread',
          'max_threads' : { 'value' : 2000, 'label' : 'Max Threads' },
          'max_docs' : { 'value' : 10, 'label' : 'Max Input Documents' },
          'threshold' : { 'value' : 0.5, 'label' : 'Threashold' }
         }      

mongodb = {
          'title' : 'Mongo DB',
          'dbhost' : { 'value' : 'localhost', 'label' : 'Mongo DB Host' },
          'dbport' : { 'value' : 27017, 'label' : 'Mongo DB Port' },
          'dbname' : { 'value' : 'events2012', 'label' : 'MongoDB-DB Name' },
          'dbcoll' : { 'value' : 'posts', 'label' : 'MongoDB-Collection' }
          }
          
parameters = {
              'lsh'     : lsh ,
              'thread'  : thread ,
              'mongodb' : mongodb  
             }


import json

@app.route('/', methods=['GET', 'POST'])
def index():
    errors = []
    results = {}
    
    if request.method == 'POST':
        #argstr = ''
        #for section in parameters:
            #for p in section.params:
            #    v = request.form[p['name']]
            #    values.append((p, v))
            #    argstr += p['name'] + '=' + v + '&'
            #if not str.isnumeric( k ) or int( k ) <= 2:
            #    errors.append( 'Invalid number of hyperplanes' )
            #flash("Your request was submitted successfuly")
            #print('redirect')
        p_str = json.dumps(parameters)
        return redirect(url_for('lsh')+'?page=0&params='+p_str) # argstr[:-1])
        
    return render_template('index.html', errors=errors, tweets=results, params=parameters)

import sys

sys.path.append("../Twitter-New-Event-Detection")
import NED

model = None

@app.route('/lsh')
def lsh():
    #flash("Please be patient...")
    results, params = lsh_run()
    #flash("done...")
    return render_template('lsh.html', threads=results, params=params)

@app.route('/lsh-json')
def lsh_json():
    results, params = lsh_run()
    return jsonify(results)
    
def lsh_run():
    p_str = request.args.get('params', type=str)
    params = json.loads(p_str)
                       
    k = request.args.get('k', type=int)
    print(k)
    params['lsh']['k']['value'] = k 
    maxB = params['lsh']['maxB']['value'] = request.args.get('maxB', type=int)
    tables = params['lsh']['tables']['value']

    epsilon = params['thread']['threshold']['value']
    max_threads = params['thread']['max_threads']['value']
    max_docs = params['thread']['max_docs']['value']

    #mongodb
    dbhost =  params['mongodb']['dbhost']['value']
    dbport =  params['mongodb']['dbport']['value']
    dbname =  params['mongodb']['dbname']['value']
    dbcoll =  params['mongodb']['dbcoll']['value']

    print(params)

    #k = request.args.get('k', type=int)
    #maxB = request.args.get('maxB', type=int)
    #tables = request.args.get('tables', type=int)
    #epsilon = request.args.get('threshold', type=float)
    #%%
    #max_threads = request.args.get('max_threads', type=int)
    #max_docs = request.args.get('max_docs', type=int)

    page =  request.args.get('page', 0, type=int)
    
    print(k, maxB, tables, epsilon, max_docs, page)
    print(model, page, max_docs, dbhost, dbport, dbname, dbcoll, max_threads)
    
    global model
    if False and (model == None or page == 0):
        model = NED.init_mongodb(k, maxB, tables, epsilon, max_docs, page)
        NED.execute(model, page, max_docs, dbhost, dbport, dbname, dbcoll, max_threads)
        
    results = model.jsonify(max_threads)
    return results, params
    
@app.route('/test')
def test():    
    errors = []

    k = request.args.get('k', 10, type=int)
    #b = request.args.get('b', 0, type=int)
    
    try:
        coll = mongo.db[collname]
        cursor = coll.find({}).limit(k)
    except Exception as e:
        errors.append(str(e))
        pass
    
    print('going to sleep')
    time.sleep(3)
    print('wake up')
    
    if cursor != None:
        
        results = {}
        results['count'] = cursor.count()
        results['values'] = values
        results['tweets'] = []
        for c in cursor:
            if c['_id'] == -1 or c.get('json', None) == None:
                continue 
            
            results['tweets'].append( { 'id' : c['_id'], 'text': c['json']['text'] } )
            
    return jsonify(result=results)

if __name__ == '__main__':
    app.run()