# -*- coding: utf-8 -*-
__author__ = 'Administrator'

from flask import Flask, render_template, redirect, request
import pymongo
from math import ceil
import requests as Requests
import json
import re
import pygraphviz as pgv
import os

master_ip = ''
mongo_ip = ''
data = json.load(file('config'))
master_ip = data['master_ip']
mongo_ip = data['mongo_ip']

class ProgressClient:
    def __init__(self):
        self.client_ = pymongo.MongoClient(mongo_ip, 27017)
        self.db_ = self.client_['logdb']
        self.col_diag_ = self.db_['diagnoseC']
        self.col_task_ = self.db_['taskfeaC']
        self.col_block = self.db_['blockfeaC']

    def getTaskFea(self,appid,taskid):
        sorted_result = self.col_task_.find({"appid":appid,"taskid":taskid})
        for item in sorted_result:
            return json.loads(item['fulldata'])

    def getBlockFea(self,appid,blockid):
        sorted_result = self.col_block.find({"appid":appid,"blockid":blockid})
        for item in sorted_result:
            return json.loads(item['fulldata'])

    def all_items(self, startIdx=0, num=10):
        # sorted_result = self.col_.find({"clusterid":"test","appid":"application_1447660331941_0109"})
        sorted_result = self.col_diag_.find().sort([
            ("appid", pymongo.DESCENDING),
            ("stageid", pymongo.ASCENDING)
        ])
        limit_result = sorted_result.skip(startIdx).limit(num)
        items = []
        for item in limit_result:
            data = item['fulldata']
            data2 = json.loads(data)
            items.append(data2)
        return items
    def oneapp_items(self, appid,startIdx=0, num=10):
        # sorted_result = self.col_.find({"clusterid":"test","appid":"application_1447660331941_0109"})
        sorted_result = self.col_diag_.find({"appid":appid}).sort([
            ("stageid", pymongo.ASCENDING)
        ])
        limit_result = sorted_result.skip(startIdx).limit(num)
        items = []
        for item in limit_result:
            data = item['fulldata']
            data2 = json.loads(data)
            items.append(data2)
        return items

    def item_count(self,appid):
        if appid=='':
            return self.col_diag_.count({})
        else:
            return self.col_diag_.find({"appid":appid}) .count()

    def close(self):
        if self.client_ is not None:
            self.client_.close()


def is_integer(num):
    try:
        int(num)
        return True
    except:
        return False

def is_appid(appid):
    try:
        print "appid:"+appid
        return True
    except:
        return False

def getDict():
    f = open('data/schemaDict')
    dict = {}
    for line in f:
        pair = line.split('@@')
        dict[pair[0]] = pair[1]
    return dict
def getfeamap(data):
    map = data['map']
    res={}
    for meta in map:
        res[meta] = map[meta]
    return res
def gettreeset(metatype):
    if metatype=='task':
        fr = open('data/treeTaskKM.dot')
    elif metatype == 'block':
        fr = open('data/treeBlockKM.dot')
    treeset = set()
    for line in fr:
        pattern = re.compile(r'.*label="(.*\..*\d+)".*')
        match = pattern.match(line)
        if match:
            treeset.add(match.group(1))
    return treeset

def checktreepng():
    # if os.path.isfile('static/treeTaskKM.png'):
    #     return
    A=pgv.AGraph('data/treeBlockKM.dot') # create a new graph from file
    A.layout("dot") # layout with default (neato)
    A.draw('static/treeBlockKM.png') # draw png
    print("Wrote treeBlockKM.png")
    B=pgv.AGraph('data/treeTaskKM.dot') # create a new graph from file
    #B.node_attr['fixedsize']='false'
    #B.node_attr['fontcolor']='#000000'
    B.layout("dot") # layout with default (neato)
    B.draw('static/treeTaskKM.png') # draw png
    print("Wrote treeTaskKM.png")


app = Flask(__name__)
@app.route('/detail')
def detail():
    metatype = request.args.get('metatype', None)
    checktreepng()
    clusterid=request.args.get('clusterid', None)
    appid=request.args.get('appid', None)
    #appid = appid if is_appid(appid) else 'nullappid'
    metaid=request.args.get('metaid', None)
    metaid = metaid.replace('%20',' ')
    client = ProgressClient()
    dict = getDict()
    if metatype=='task':
        feamap = getfeamap(client.getTaskFea(appid,metaid))
    elif metatype == 'block':
        feamap = getfeamap(client.getBlockFea(appid,metaid))
    client.close()
    dataset = feamap.values()
    items=[]
    index=0
    for key in feamap:
        item=[index,key,feamap[key],dict[key]]
        items.append(item)
        index=index+1
    treeset = gettreeset(metatype)
    treemap={}
    for key in treeset:
        treemap[key] = dict[key]
    return render_template('detail.html',appid=appid,metaid=metaid,items = items,dataset = json.dumps(dataset),treemap=treemap,metatype=metatype)

@app.route('/')
def hello(name=None):
    startStr = request.args.get('startIdx', None)
    startIdx = int(startStr) if is_integer(startStr) else 0
    appid = request.args.get('appid', None)
    appid = appid if is_appid(appid) else ''
    client = ProgressClient()
    if appid=='':
        items = client.all_items(startIdx)
    else:
        items = client.oneapp_items(appid,startIdx)
    page_count = int(ceil(client.item_count(appid) / 10.0))
    active_page = int(ceil( (startIdx + 1) / 10.0 ))
    client.close()
    return render_template('webpage.html', items=items,
                           page_count=page_count, active_page=active_page,app_id=appid)

@app.route('/submit/', methods=['POST'])
def submit():
    if request.form.get('clusterid') is not None\
       and request.form.get('appid') is not None:
        cluster_id = request.form['clusterid']
        app_id = request.form['appid']
        Requests.post('http://'+master_ip+':8890/diagnose',
                      data={'clusterid':cluster_id,'appid': app_id})
        return redirect('/?appid='+app_id)
    else:
        return u"缺少参数"
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)