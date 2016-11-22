#import os
from flask import Flask, flash, redirect, render_template, request, url_for, jsonify
from flask_pymongo import PyMongo
import time

import json
import copy
import sys



app = Flask(__name__)

app.config['MONGO_HOST'] = 'localhost'
app.config['MONGO_PORT'] = 27017

app.config['MONGO_DBNAME'] = 'logger'
app.config['TEMPLATES_AUTO_RELOAD'] = True
collname = 'runs'

app.secret_key = 'some_secret'

mongo = PyMongo(app)



lsh = {
          'title' : 'LSH parameters',
          'k' :         { 'value' : 13, 'label' : 'Hyperplanes' } ,
          'maxB' :      { 'value' : 500, 'label' : 'Max bucket size' } ,
          'tables' :    { 'value' : 64, 'label' : 'Number of Hashtables' } ,
          'run' :       {'value' : 0, 'label' : 'Forground'} 
      }

thread = {
          'title' : 'Thread',
          'max_threads' : { 'value' : 2000, 'label' : 'Max Threads' },
          'max_docs' : { 'value' : 10, 'label' : 'Max Input Documents' },
          'threshold' : { 'value' : 0.6, 'label' : 'Threashold' }
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


@app.route('/', methods=['GET', 'POST'])
def index():
    errors = []
    results = {}
    
    if request.method == 'POST':
        argstr = ''
        #params = copy.deepcopy( parameters )
        for cntrl in request.form:
            #print (cntrl, request.form[cntrl])
            argstr += cntrl + '=' + request.form[cntrl] + '&'
        argstr = argstr[:-1]  # remove redundant '&' char

        if request.form['run']=='1' or request.form['run']==1:
            return redirect(url_for('lsh')+'?'+argstr)

        return redirect(url_for('lsh_bg')+'?'+argstr)
        
    return render_template('index.html', errors=errors, tweets=results, params=parameters)


sys.path.append("../Twitter-New-Event-Detection")
import NED

model = None

@app.route('/lsh')
def lsh():
    #flash("Please be patient...")
    threads, tables, params = lsh_run()
    #flash("done...")
    return render_template('lsh.html', threads=threads, params=params, tables=tables)

import multirun
@app.route('/lsh_bg')
def lsh_bg():
    flash("Refresh from time to time...")
    
    lsh_run(bg=True)
    
    #flash("done...")
    return redirect(url_for('runs'))

#import pprint 

@app.route('/lsh-json')
def lsh_json():
    threads, tables, params = lsh_run()
    information = {}
    information['threads'] = threads
    information['tables'] = tables
    #pprint.pprint(tables)
    return jsonify(information)
    
def lsh_run(bg=False):

    params = copy.deepcopy( parameters )

    for p in request.args:
        for section in params:
            for param in params[section]:
                if param == p:
                    mytype = type(params[section][param]['value'])
                    params[section][param]['value'] = request.args.get(p, type=mytype)
                    
    max_threads = request.args.get('max_threads', type=int)
    k = request.args.get('k', type=int)
    maxB = request.args.get('maxB', type=int)
    tables = request.args.get('tables', type=int)
    epsilon = request.args.get('threshold', type=float)
    #%%
    max_docs = request.args.get('max_docs', type=int)

    dbhost = request.args.get('dbhost', type=str)
    dbport = request.args.get('dbport', type=int)
    dbcoll = request.args.get('dbcoll', type=str)
    dbname = request.args.get('dbname', type=str)

    page =  request.args.get('page', 0, type=int)

    #save to database
    #timestamp = time.time()
    coll = mongo.db[collname]
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    run_id = 'LSH'+ started.replace('-', '').replace(' ', '').replace(':', '')
    coll.insert_one({ '_id' : run_id, 
                      'started' : started, 
                      'ended' : '',
                      'status': 'New', 
                      'threads' : {}, 
                      'tables': {},
                      'params' : params
                     })
    print( 'Parameters', k, maxB, tables, epsilon, max_docs, page )
    model = NED.init_mongodb(k, maxB, tables, epsilon, max_docs, page)
    coll.update_one({ '_id': run_id }, 
                    { '$set': {
                               'status': 'Running'
                               }
                    }, upsert=False)
    
    if bg == True:
        invokes = []
        invokes.append( (execute, model, page, max_docs, dbhost, dbport, dbname, dbcoll, max_threads, coll, run_id, params) )
        multirun.run_bg(invokes)
        return 
    
    return execute(model, page, max_docs, dbhost, dbport, dbname, dbcoll, max_threads, coll, run_id, params)


def execute(model, page, max_docs, dbhost, dbport, dbname, dbcoll, max_threads, coll, run_id, params):    
    threads = tables = {}
    print ( page, max_docs, dbhost, dbport, dbname, dbcoll, max_threads, coll, run_id, params )
    try:
        NED.execute(model, page, max_docs, dbhost, dbport, dbname, dbcoll, max_threads)
            
        threads, tables = model.jsonify(max_threads)
        coll.update_one({ '_id': run_id }, 
                        { '$set': {
                                   'status': 'Finished',
                                   'ended' : time.strftime("%Y-%m-%d %H:%M:%S"),
                                   'threads': threads,
                                   }
                        }, upsert=False)
    except Exception as e:
        coll.update_one({ '_id': run_id }, 
                        { '$set': {
                                   'status' : 'Failed',
                                   'error' : str(e)
                                   }
                        }, upsert=False)
        
    
    try:
        coll.update_one({ '_id': run_id }, 
                        { '$set': {
                                   'tables' : tables
                                   }
                        }, upsert=False)
    except Exception as e:
        coll.update_one({ '_id': run_id }, 
                        { '$set': {
                                   'status' : 'Warning',
                                   'error' : str(e)
                                   }
                        }, upsert=False)
        pass
        
    return threads, tables, params
    
@app.route('/display')
def logs_run():  
    errors = []
    threads = {}
    params = {}
    tables = {}

    run_id = request.args.get('id', None, type=str)
    if run_id == None:
        errors.append('Parameter is missing: id')
        return jsonify(errors=errors)
        
    try:
        coll = mongo.db[collname]
        print(run_id)
        cursor = coll.find({'_id' : run_id})
        if cursor != None:
            #print(cursor.count())
            for c in cursor:
                threads = c['threads']
                params = c['params']
                tables = c['tables']
                #print (tables)
    except Exception as e:
        errors.append(str(e))
        pass
    

    return render_template('lsh.html', threads=threads, params=params, tables=tables)
            
    #return jsonify(runs=runs, errors=errors)

    
@app.route('/runs')
def runs():  
    errors = []
    runs = []
    page = request.args.get('page', 0, type=int)
    pagesize = request.args.get('pagesize', 10, type=int)
    
    
    try:
        coll = mongo.db[collname]
        cursor = coll.find({}).skip(page * pagesize)#.sort({'_id' : 1})
        if cursor != None:
            for c in cursor:
                temp = {}
                temp['_id'] = c['_id']
                temp['status'] = c['status']
                temp['started'] = c['started']
                temp['ended'] = c.get('ended', '')
                temp['params'] = c['params']
                runs.append(temp)
        
    except Exception as e:
        errors.append(str(e))
        raise
    
    return render_template('runs.html', runs=runs, errors=errors)
            
    #return jsonify(runs=runs, errors=errors)

if __name__ == '__main__':
    app.run()