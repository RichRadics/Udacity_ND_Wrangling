
# coding: utf-8

# In[92]:

import pprint
import datetime
import time
from pymongo import MongoClient

client = MongoClient('192.168.0.29:27017')
db = client['test']

def do_aggregate(collection, query):
    cursor = collection.aggregate(query)
    return [x for x in cursor]


# In[ ]:

# 1. Total record count
print 'Record count'
print db.liverpool.count()
print '\n'


# In[ ]:

# 2. Count of nodes/ways
print 'Node/way element frequency'
pipeline = [{'$match':{'$or':[{'type':"way"},{'type':"node"}]}},
             {'$group': {'_id': '$type', 'count': {'$sum':1}}},
             {"$limit": 2}]

agg1 = do_aggregate(db.liverpool, pipeline)
for x in agg1:
    print x['_id'], '\t', x['count']
print '\n'
   


# In[ ]:


# 3. Unique users    
print 'Unique users:'
print len(db.liverpool.distinct('created.user'))
print '\n'


# In[ ]:

# 4. Top 5 contributors as percentage of contributions
totalUserPosts=db.liverpool.count({"created.user": {"$exists": True}})
pipeline = [{"$match": {"created.user": { "$exists": True }}},
            {"$group":{"_id":"$created.user","count":{"$sum":1}}},
            {"$project":
                {"count":1,"percentage":{"$multiply":[{"$divide":[100,totalUserPosts]},"$count"]}}
            },
            {"$sort" : {"count": -1}},
            {"$limit": 5}]

    
agg2 = do_aggregate(db.liverpool, pipeline)
print 'Users by contribution percentage'
for x in agg2:
    print x['_id'], x['count'], "%.2f" % x['percentage']
print '\n'


# In[131]:

# 5. Top 10 months for contributions 
pipeline = [{"$match": {"created.user": { "$exists": True }}},
            {'$project':
                {'username': '$created.user',
                'year': { '$year': "$created.timestamp" },
                'month': { '$month': "$created.timestamp" }
                }},
            {'$group':{'_id': {'year':'$year', 'month':'$month', 'username':'$username'}, 'count':{'$sum':1}}},
            {'$sort': {'count':-1}},
            {'$limit': 10}]
agg3 = do_aggregate(db.liverpool, pipeline)
print 'Top 10 months for contributions'
for x in agg3:
    print '%s\t%s\t%s\t%d' % (x['_id']['year'], x['_id']['month'], x['_id']['username'],  x['count'])


# In[157]:

# Postcode re-assessment
import re
postcode_re = re.compile(r'^(GIR ?0AA|[A-PR-UWYZ]([0-9]{1,2}|([A-HK-Y][0-9]([0-9ABEHMNPRV-Y])?)|[0-9][A-HJKPS-UW]) ?[0-9][ABD-HJLNP-UW-Z]{2})$')
pipeline = [{'$match': {'address.postcode':{'$exists':True}, }},
            {'$match': {'address.postcode':{'$not': postcode_re}}},
            {'$project': {'postcode':'$address.postcode'}},
            {'$group': {'_id': '$postcode', 'count':{'$sum':1}}},
            {'$project': {'postcode':'$_id', 'count':'$count'}},
            {'$limit': 20}]
            
res = do_aggregate(db.liverpool,pipeline)
print 'Invalid postcodes'
for x in res:
    print x['postcode'], x['count']


# In[159]:

res = do_aggregate(db.liverpool, 
                   [{'$match':{'address.postcode':{'$exists':True}}},
                    {'$project':{'postcode':'$address.postcode'}}])


# In[174]:

prefix = set()
print 'Total postcodes: %d' % len(res)
for x in res:
    prefix.add( x['postcode'].split(' ')[0])
print 'Unique postcode prefixes'
pprint.pprint(prefix)


# In[182]:

bob='colin.'
print bob[::-1][1:][::-1]


# In[ ]:



