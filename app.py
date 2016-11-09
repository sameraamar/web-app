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


parameters = [ 
              [
               'LSH Parameters:', 
               {'name' : 'k', 'default' : 10, 'label' : 'Hyperplane', } ,
               {'name' : 'maxB', 'default' : 500, 'label' : 'Max bucket size', 'placeholder' : ''} ,
               {'name' : 'tables', 'default' : 64, 'label' : 'Number of Hashtables', 'placeholder' : ''} ,
               {'name' : 'maxB', 'default' : 500, 'label' : 'Max bucket size', 'placeholder' : ''} 
              ]
              ,
              [
               'Thread Parameters:', 
               {'name' : 'max_threads', 'default' : 2000, 'label' : 'Max Threads', 'placeholder' : ''} ,
               {'name' : 'max_docs', 'default' : 10, 'label' : 'Max Input Documents', 'placeholder' : ''} ,
               {'name' : 'threshold', 'default' : 0.5, 'label' : 'Threashold', 'placeholder' : ''} 
              ]
              ,
              [
               'Connection Details:', 
               {'name' : 'dbhost', 'default' : 'localhost', 'label' : 'Mongo DB Host', 'placeholder' : ''} ,
               {'name' : 'dbport', 'default' : 27017, 'label' : 'Mongo DB Port', 'placeholder' : ''} ,
               {'name' : 'dbname', 'default' : 'events2012', 'label' : 'MongoDB-DB Name', 'placeholder' : ''} ,
               {'name' : 'dbcoll', 'default' : 'posts', 'label' : 'MongoDB-Collection', 'placeholder' : ''} 
               #{'name' : 'page', 'default' : 0, 'label' : 'Page', 'placeholder' : ''} 
              ]              
             ]

@app.route('/', methods=['GET', 'POST'])
def index():
    errors = []
    results = {}
    
    if request.method == 'POST':
        argstr = ''
        for section in parameters:
            for p in section:
                if type(p) is str:
                    continue
                
                v = request.form[p['name']]
                values.append((p, v))
                argstr += p['name'] + '=' + v + '&'
            #if not str.isnumeric( k ) or int( k ) <= 2:
            #    errors.append( 'Invalid number of hyperplanes' )
            #flash("Your request was submitted successfuly")
            #print('redirect')
        return redirect(url_for('lsh')+'?'+argstr[:-1])
        
    return render_template('index.html', errors=errors, tweets=results, params=parameters)

import sys

sys.path.append("../Twitter-New-Event-Detection")
import NED

model = None

@app.route('/lsh')
def lsh():
    #flash("Please be patient...")
    results = lsh_run()
    #flash("done...")
    return render_template('lsh.html', threads=results)

@app.route('/lsh-json')
def lsh_json():
    results = lsh_run()
    return jsonify(results)
    
def lsh_run():
    k = request.args.get('k', type=int)
    maxB = request.args.get('maxB', type=int)
    tables = request.args.get('tables', type=int)
    epsilon = request.args.get('threshold', type=float)
    #%%
    max_threads = request.args.get('max_threads', type=int)
    max_docs = request.args.get('max_docs', type=int)
    
    #%%
    #mongodb
    dbhost =  request.args.get('dbhost', type=str)
    dbport =  request.args.get('dbport', type=int)
    dbname =  request.args.get('dbname', type=str)
    dbcoll =  request.args.get('dbcoll', type=str)
    page =  request.args.get('page', 0, type=int)
    
    print('NED run...')
    if model == None or page == 0:
        global model
        
        model = NED.init_mongodb(k, maxB, tables, epsilon, max_docs, page)
        NED.execute(model, page, max_docs, dbhost, dbport, dbname, dbcoll, max_threads)
        
    results = model.jsonify(max_threads)
    return results
    
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