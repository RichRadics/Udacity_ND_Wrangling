
# coding: utf-8

# In[ ]:

# Source file from https://mapzen.com/data/metro-extracts https://s3.amazonaws.com/metro-extracts.mapzen.com/liverpool_england.osm.bz2


# In[3]:

# Import required libraries
import xml.etree.cElementTree as ET
import pprint
import re
from collections import defaultdict
import codecs
import json

# Declare globals
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
### DOCNOTE regex below taken from http://stackoverflow.com/questions/164979/uk-postcode-regex-comprehensive, answer provided by Colin
### DOCNOTE tested with regex101.com
postcode_re = re.compile(r'^(GIR ?0AA|[A-PR-UWYZ]([0-9]{1,2}|([A-HK-Y][0-9]([0-9ABEHMNPRV-Y])?)|[0-9][A-HJKPS-UW]) ?[0-9][ABD-HJLNP-UW-Z]{2})$')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
expectedStreetTypes = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Close", "Terrace", 'Grove','Crescent', 'Way', 'Mews','View']


# In[4]:

# Utility functions to create sample files
def get_element_for_sample(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag

    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()
            
def create_sample_file(osm_file, step = 10):
    sample_file = "{0}.sample".format(osm_file)
    with open(sample_file, 'wb') as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write('<osm>\n  ')
        # Write every 10th top level element
        for i, element in enumerate(get_element_for_sample(osm_file)):
            if i % step == 0:
                output.write(ET.tostring(element, encoding='utf-8'))
        output.write('</osm>')
    return sample_file
    




# In[5]:

# Auditing functions
def audit_street_type(in_dict, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expectedStreetTypes:
            in_dict[street_type].add(street_name)

def audit_postcode(in_dict, postcode):
    if not postcode_re.match(postcode):
        in_dict[postcode].add(postcode)


def is_street_name(elem):
    # Does this tag have a 'street' key?
    return (elem.attrib['k'] == "addr:street")

def is_postcode(elem):
    # Does this tag have a 'postcode' key?
    return (elem.attrib['k'] == "addr:postcode")


def audit(osmfile, audit_type = 'streetnames'):
    # Audit shell
    # Open the file, search for 'node' or 'way' nodes, then check for audit items
    osm_file = open(osmfile, "r")
    # Define empty result dictionary
    res = defaultdict(set)
    for _, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if audit_type=='streetnames':
                    if is_street_name(tag):
                        audit_street_type(res, tag.attrib['v'])
                if audit_type=='postcodes':
                    if is_postcode(tag):
                        audit_postcode(res,tag.attrib['v'])
        # Important! Must call 'clear' method when working with very large datasets to avoid seg faults
        elem.clear()
    return res


# In[6]:

# Final file processing 
def shape_element(element):
    # Function to convert useful data in an XML element into JSON, simply by building a dictionary
    # Taken (and adapted) from the Lesson 6 scripts
    node = {}
    # Only interested in 'node' and 'way' elements
    if element.tag == "node" or element.tag == "way" :
        node['type']=element.tag
        for el in element.iter():
            if el.tag=='tag':
                # special tag parsing
                k = el.get('k')
                v = el.get('v')
                if not problemchars.match(k):
                    # Break the 'addr' keys into a child set
                    if k.startswith('addr:'):
                        addr=k.split(':')
                        if len(addr)==2:
                            if 'address' not in node: node['address']={}
                            #################  DATA CLEANSING ################    
                            if addr[1]=='postcode':
                                # Postcode cleaning - remove trailing special characters    
                                if problemchars.match(v[::-1][0]): v = v[::-1][1:][::-1]
                            #################################################    
                            node['address'][addr[1]]=v
                    else:
                        node[k]=v
            else:
                # 'normal' elements
                for at in el.attrib:
                    if at in CREATED:
                        if 'created' not in node: node['created']={}
                        node['created'][at]=el.get(at)
                    elif at in {'lat','lon'}:
                        if 'pos' not in node: node['pos']=[]
                        node['pos'].insert(0,float(el.get(at)))
                    elif element.tag=='way' and el.tag=='nd' and at=='ref':
                        if 'node_refs' not in node: node['node_refs']=[]
                        node['node_refs'].append(el.get(at))
                    else:
                        node[at]=el.get(at)
        return node
    else:
        return None


def process_map(file_in, pretty = False):
    # Parse an input XML file into JSON
    file_out = "{0}.json".format(file_in)
    data = []
    with open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in, ('start',)):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
            element.clear()
    return data


# In[8]:

# 1. Sample file + audits
source_file = 'liverpool_england.osm'
# Create a 1/30th scale sample file - this fits the 1-10MB size requirement
sample_file = create_sample_file(source_file,50)

# Generate audits for postcodes and street names
audit_streets = audit(sample_file, 'streetnames')
audit_postcodes = audit(sample_file, 'postcodes')

# Create a sample JSON file
process_map(sample_file)


# In[19]:

# Examine the audit results
pprint.pprint(dict(audit_streets))
pprint.pprint(dict(audit_postcodes))


# In[ ]:

# 2. Run the JSON conversion for the full map
process_map(source_file)

