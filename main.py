import requests
import json
import jira
import sprintly
import distance
import pprint

***REMOVED***
***REMOVED***


def get_jir_user_email_map( project, auth ):
    api_call = JIRA_API_URI + '/user/permission/search?permissions=COMMENT_ISSUE&projectKey=%s&username='%project
    req = requests.get( api_call, auth=auth )
    req.raise_for_status()
    
    jira_users = json.loads(req.content)
    return { user['emailAddress'] : user for user in jira_users }
    

def map_users_spr_to_jir( sprintly_map, jira_map ):
    return { user['id'] : jira_map[user['email']]['name'] for (key,user) in sprintly_map.iteritems() if jira_map.has_key(user['email']) }    


#def do_user_mapping( sprintly_auth, jira_auth ):
#    
#    sprintly_map = get_sprintly_user_email_dict_for( product, sprintly_auth )
#    jira_map     = get_jira_user_email_dict_for( project, jira_auth )
#    return map_users_spr_to_jira


def get_jir_projs( auth ):
    api_call = JIRA_API_URI + '/user/permission/search?permissions=COMMENT_ISSUE&projectKey=%s&username='%(project)



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


def map_with( collection, key=None, get_key=None ):
    if not get_key and key:
        get_key = lambda x : x[key]

    if not get_key:
        raise ValueError( "Either key or get_key arg must be set" )

    return { get_key(item) : item for item in collection }


def import_jira_issue( sprintly_product, jira_issue ):
    #sprintly_product
    pass

def import_jira_project( jira_project, sprintly_project=None ):
    
    #if
    #spr_client

    for jira_issue in jira_project:
        if not spr_project.has_issue( jira_issue ):
            import_jira_issue( spr_product, jira_issue )
        else:
            print "Issue %s already exists in sprintly product: %s"%(jira_issue,spr_product)

def write_out_json( file_name, data_dict ):
    json_file = open( file_name, 'w+' )
    json_file.write( json.dumps( data_dict, indent=4, separators=(',', ': ') ) )
    json_file.close()

def find_tag( tag_name, spr_items ):
    for item in spr_items:
        for tag in item.tags:
            if tag is tag_name:
                return item


class JiraToSprintlyImporter():

    def __init__(self, jira_auth, sprintly_auth):
        self.jir_client = jira.client.JIRA( options=jira_options, basic_auth=jira_auth )
        self.spr_client = sprintly.Client( sprintly_auth )

        self.jir_projs = map_with( self.jir_client.projects(), get_key=lambda x:x.raw['name'] )
        self.spr_prods = map_with( self.spr_client.products(), get_key=lambda x:x.raw['name'] )

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
        auto_map = guess_mapping( self.jir_projs, self.spr_prods )     
        prod_map = dict(auto_map) #FIXME
        
        print "Product map: "
        print json.dumps( prod_map, indent=4, separators=(',', ': ') )
        
        self.config['product_map'] = prod_map
        self.write_config()

        self.config['people_maps'] = {}
        for (jir_proj_name,spr_prod_name) in prod_map.iteritems():
            print
            jir_proj = self.jir_projs[jir_proj_name]
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

            spr_prod = self.spr_prods[spr_prod_name]
            spr_people = spr_prod.people()
            
            api_call = 'user/permission/search?permissions=COMMENT_ISSUE&projectKey=%s&username='%jir_proj.key
            rq = requests.get( self.jir_client._get_url( api_call ), auth=self.jir_client._session.auth )
            jir_users  = [ jira.client.User( self.jir_client._options, self.jir_client._session, data ) for data in json.loads( rq.content ) ]

            spr_people_map = map_with( spr_people, get_key=lambda x:x.email )
            jir_users_map  = map_with( jir_users,  get_key=lambda x:x.emailAddress )

            people_map = guess_mapping( jir_users_map, spr_people_map )

            pprint.pprint( "People map: " )
            print json.dumps( people_map, indent=4, separators=(',', ': ') )

            self.config['people_maps'][jir_proj_name] = people_map
            self.write_config()

        return self.config
            

    def do_import(self,projects=None,config=None) :  
        config=self.read_config()

        if projects is None:
            projects = config['product_map']

        #for (jir_proj_name,spr_prod_name) in config['product_map'].iteritems():
        for jir_proj_name in projects:
            spr_prod_name = config['product_map'].get(jir_proj_name,False)
            
            if spr_prod_name is False:
                print "Mapping for jira proj %s says False. Skipping"%jir_proj_name
                continue   
                
            spr_prod = None
                
            if spr_prod_name is None:
                print "Mapping for jira proj [{name}] is Null. Creating new Sprintly product named [{name}]".format(name=jir_proj_name)
                spr_prod = self.spr_client.create_product( jir_proj_name )
            elif spr_prod_name not in self.spr_prods:
                print "Mapping for jira proj [%s] is [%s], but does not exist. Creating new Sprintly product"%(jir_proj_name,spr_prod_name)
                spr_prod = self.spr_client.create_product( spr_proj_name )
            else:
                print "Mapping for jira proj [%s] is [%s]"%(jir_proj_name,spr_prod_name) 
                spr_prod = self.spr_prods[spr_prod_name]

            jir_proj = self.jir_projs[jir_proj_name]
            print "Downloading JIRA items for [%s]"%jir_proj.name
            jir_issues = self.jir_client.search_issues('project=%s'%jir_proj.key)
            spr_items  = spr_prod.items()
            
            #pitem_tag_map = map_with( pitems, get_key=lambda x: x.tag )
            for jir_issue in jir_issues:
                print "Issue %s: %s"%(jir_issue.key, jir_issue.raw['fields']['summary'])
                spr_item = find_tag( jir_issue.key, spr_items )
                if spr_item is not None:
                    print "Spr Item found, not creating new item"
                    continue

                print "Would create item here"
                #spr_prod.create_item( convert_to_sprintly( jir_issue ) )
            #    print '\n'.join( [ str(item.raw)  for item in spr_prod.items() ] )
            #    if spr_prod.search_issue('tag=%s'%jissue.key):
            #        print "Converting issue %s:%s"%(jissue.key,jissue.title)







