import distance
import itertools
import jira
import jira_monkeypatch
#import json
import simplejson as json
import pprint
import re
import requests
import sprintly
import sys
from collections import defaultdict

jira_monkeypatch.monkeypatch_jira()

def grouper(iterable, n, fillvalue=None):
    # taken from itertools recipes
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)



def guess_mapping( set_a, set_b, dist_algo=distance.jaccard ):
    a_to_b          = {}
    remaining_a     = list(set_a)
    remaining_b     = list(set_b)
    ranked_mappings = []
    for a_item in set_a:
        for b_item in set_b:
            case_dist   = dist_algo( a_item, b_item )
            nocase_dist = dist_algo( a_item.lower(), b_item.lower() )
            agg_dist    = nocase_dist + case_dist / 10.0

            ranked_mappings.append( (agg_dist, a_item, b_item) )

    ranked_mappings.sort()

    for mapping in ranked_mappings:
        if mapping[1] in remaining_a and mapping[2] in remaining_b:      # if the best is still available for mapping
            remaining_a.remove( mapping[1] ) # remove it from availability
            remaining_b.remove( mapping[2] ) # remove it from availability
            a_to_b[mapping[1]] = mapping[2]  # and map a to b

    for a_item in remaining_a: #mark missing mappings as None
        a_to_b[a_item] = None

    return a_to_b


def map_key( collection, get_key=None ):
    if not get_key:
        raise ValueError( "get_key arg must be set" )

    return { get_key(item) : item for item in collection }
            
            
def multimap_multikey( collection, get_keys ):
    key_map = {}
    for item in collection:
        for key in get_keys( item ):
            if not key_map.has_key( key ):
                key_map[key] = []

            key_map[key].append( item )

    return key_map


def write_out_json( file_name, data_dict ):
    json_file = open( file_name, 'w+' )
    json_file.write( json.dumps( data_dict, indent=4, separators=(',', ': ') ) )
    json_file.close()


class JiraToSprintlyConverter():
    def __init__(self,jir_users, spr_people):
        self.jir_user_map   = map_key( jir_users,  get_key=lambda x:x.emailAddress )
        self.spr_person_map = map_key( spr_people, get_key=lambda x:x.email )

        self.jir_users      = map_key( jir_users, get_key=lambda x:x.key )

    def convert_issuetype(self,jira_issue):
        if len(jira_issue.raw['fields']['subtasks']) > 0:
            return 'story'

        issuetype = jira_issue.raw['fields']['issuetype']['name']
        type_lookup = { 
           'epic'        :'story',
           'new feature' :'task',
           'bug'         :'defect',
           'task'        :'task',
           'sub-task'    :'task',
            #:'test',
        }
        
        return type_lookup[issuetype.lower()]
    
    def convert_status(self, jira_issue):
        status = jira_issue.raw['fields']['status']['name']
        status_lookup = { 
            'open'  : 'backlog',
            'to do' : 'backlog',
            'done'  : 'completed',
            'in progress' : 'in-progress',
            #:'in-progress',
            #:'completed',
            #:'accpted',
        }
        
        return status_lookup[status.lower()]
    
    def lookup_person(self, email_address):
        try:
            return self.spr_person_map[email_address].id
        except KeyError:
            try:
                jir_name = self.jir_user_map[email_address].displayName.split()
            except KeyError:
                return email_address 
            return {
                'first_name' : jir_name[0],
                'last_name'  : jir_name[1],
                'email'      : email_address,
                'admin'      : False,
            }
    
    def jira_issue_to_sprintly(self, jira_issue ):
        jira_fields = jira_issue.raw['fields']

        reporter = jira_fields['reporter']['emailAddress']
       
        spr_data = {} 
        spr_data['type']        = self.convert_issuetype( jira_issue )
        spr_data['title']       = jira_issue.raw['fields']['summary']
        #spr_data['who']
        #spr_data['what']
        #spr_data['why']
        spr_data['description'] = jira_fields['description']
        #spr_data['score']       
        spr_data['status']      = self.convert_status(   jira_issue   )
        spr_data['assigned_to'] = self.lookup_person( jira_fields['assignee']['emailAddress'] )
        spr_data['tags']        = ','.join( [jira_issue.key, 'reporter-%s'%reporter] )

        return spr_data

    def jira_comment_to_sprintly(self, jira_comment):
        parts = re.split( '\[~(\w*)\]', jira_comment.body ) 
        
        for idx in range(len(parts))[1::2]:
            match = parts[idx]
            spr_person = self.spr_person_map.get( self.jir_users[match].emailAddress )
            parts[idx] = '@[%s %s](pk:%s)'%(spr_person.first_name,spr_person.last_name,spr_person.id) 
       
        body = ''.join(parts) 
        return { 'body' : body }

class JiraToSprintlyImporter():

    def __init__(self, jira_auth, sprintly_auth):
        self.jir_client  = jira.client.JIRA( options=jira_options, basic_auth=jira_auth )
        self.spr_client  = sprintly.Client( sprintly_auth )
        self.spr_clients = { auth[0] : sprintly.Client( auth ) for auth in sprintly_auths.iteritems() }

        self.config_file_name = 'config.json'
        self.config = {}

    def write_config(self):
        write_out_json( self.config_file_name, self.config )

    def read_config(self):
        json_file = open( self.config_file_name, 'r' )
        config = json.load( json_file )
        json_file.close()

        return self.config

    def build_mappings(self):
        jir_proj_lookoup = map_key( self.jir_client.projects(), get_key=lambda x:x.raw['name'] )
        spr_prod_lookoup = map_key( self.spr_client.products(), get_key=lambda x:x.raw['name'] )
        
        auto_map = guess_mapping( jir_proj_lookoup, spr_prod_lookoup )     
        prod_map = dict(auto_map) #FIXME
        
        print "Product map: "
        print json.dumps( prod_map, indent=4, separators=(',', ': ') )
        
        self.config['product_map'] = prod_map
        self.write_config()
            
        spr_people = self.spr_client.all_people() # spr_prod.people()
        jir_users  = self.jir_client.get_all_users() # get_users(jir_proj.key)

        spr_person_map = map_key( spr_people, get_key=lambda x:x.email )
        jir_user_map  = map_key( jir_users,  get_key=lambda x:x.emailAddress )

        person_map = guess_mapping( jir_user_map, spr_person_map )
            
        pprint.pprint( "People map: " )
        print json.dumps( person_map, indent=4, separators=(',', ': ') )

        self.config['person_maps'] = {}
        for (jir_proj_name,spr_prod_name) in prod_map.iteritems():
            print
            jir_proj = jir_proj_lookoup[jir_proj_name]
            if spr_prod_name:
                print "JIRA proj: %s mapped to %s"%(jir_proj_name,spr_prod_name)
                print "Using existing sprintly product %s"%(spr_prod_name)
            else:
                opt = raw_input( "JIRA proj: %s not mapped. [Skip/Create]"%(jir_proj_name) )
                
                if len(opt) and opt.lower()[0] == 's':
                    prod_map[jir_proj_name] = False
                    print "skipping";
                else :
                    prod_map[jir_proj_name] = None
                    print "marking for creation"
                continue

            spr_prod = spr_prod_lookoup[spr_prod_name]

            self.config['person_maps'][jir_proj_name] = person_map
            self.write_config()

        return self.config
            

    def do_import(self,projects=None,config=None) :  
        if not config:
            print "no config passed. Reading from disk"
            config=self.read_config()

        if projects is None:
            projects = config['product_map']

        print "Retrieiving projects"
        jir_projs = self.jir_client.projects()
        spr_prods = self.spr_client.products()
         
        jir_proj_lookoup = map_key( jir_projs, get_key=lambda x:x.raw['name'] )
        spr_prod_lookoup = map_key( spr_prods, get_key=lambda x:x.raw['name'] )
       
        print "Retrieving users"
        jir_users  = self.jir_client.get_all_users(projects=jir_projs)
        spr_people = self.spr_client.all_people(products=spr_prods) 
            
        jir_user_map   = map_key( jir_users,  get_key=lambda x:x.emailAddress )
        spr_person_map = map_key( spr_people, get_key=lambda x:x.email )
            
        converter = JiraToSprintlyConverter( jir_users, spr_people )

        for jir_proj_name in projects:
            spr_prod_name = config['product_map'].get(jir_proj_name,False)
            
            if spr_prod_name is False:
                print "Mapping for jira proj %s says False. Skipping"%jir_proj_name
                continue   
                
            spr_prod = None
                
            if spr_prod_name is None:
                print "Mapping for jira proj [{name}] is Null. Creating new Sprintly product named [{name}]".format(name=jir_proj_name)
                spr_prod = self.spr_client.create_product( jir_proj_name )
            elif spr_prod_name not in spr_prod_lookoup:
                print "Mapping for jira proj [%s] is [%s], but does not exist. Creating new Sprintly product"%(jir_proj_name,spr_prod_name)
                spr_prod = self.spr_client.create_product( spr_proj_name )
            else:
                print "Mapping for jira proj [%s] is [%s]"%(jir_proj_name,spr_prod_name) 
                spr_prod = spr_prod_lookoup[spr_prod_name]

            jir_proj    = jir_proj_lookoup[jir_proj_name]
            print "Downloading JIRA items for [%s]"%jir_proj.name
            jir_issues  = self.jir_client.search_issues('project=%s'%jir_proj.key)
            print "Downloaded %i items"%len(jir_issues)
            spr_items   = spr_prod.items()
            spr_tag_map = multimap_multikey( spr_items, lambda x: x.tags )
            
            for jir_issue in jir_issues:
                print "Issue %s: %s"%(jir_issue.key, jir_issue.raw['fields']['summary'])
        
                jir_issue_tag = jir_issue.key.lower()
                if spr_tag_map.has_key( jir_issue_tag ):
                    assert( len(spr_tag_map[jir_issue_tag]) == 1 )
                    spr_item = spr_tag_map[jir_issue_tag][0]
                    print "Issue [%s] exists, using exsiting item"%jir_issue.key

                else:
                    spr_item_data = converter.jira_issue_to_sprintly( jir_issue )
                        
                    pprint.pprint( spr_item_data )
                    
                    assigned_to = spr_item_data['assigned_to'] 
                    if isinstance(assigned_to,basestring):
                        print "Failed to find %s. skipping issue"%assigned_to
                        continue

                    if type(assigned_to) is dict:
                        print "Assignee not found. invite required"
                        print spr_prod.create_person( assigned_to ).raw

                    author_email = jir_issue.fields.creator.emailAddress
                    item_spr_client = self.spr_clients.get(author_email)
                    if not item_spr_client:
                        print "No client for %s, using default %s"%(author_email,sprintly_auth[0])

                    spr_item =  spr_prod.create_item(spr_item_data, client=item_spr_client)

                jir_comments    = self.jir_client.comments( jir_issue.id )
                spr_comments    = spr_item.comments()
                spr_comment_map = map_key( spr_comments, get_key=lambda x: hash(x.body) )

                for jir_comment in jir_comments:
                    if spr_comment_map.has_key(hash(jir_comment.body)):
                        print "Comment already exists"
                    else:
                        author_email       = jir_comment.author.emailAddress
                        comment_spr_client = self.spr_clients.get(author_email)
                        if not comment_spr_client:
                            print "No client for %s, using default %s"%(author_email,sprintly_auth[0])

                        spr_comment_data   = converter.jira_comment_to_sprintly(jir_comment)
                        spr_comment        = spr_item.create_comment( spr_comment_data, client=comment_spr_client )
                    #print spr_comment.raw

