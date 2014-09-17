import requests
import json
import jira
import sprintly
import distance

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


def get_jira_projects( auth ):
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
    

def test_jira_to_sprintly(jira_auth, sprintly_auth):
    jira_client       = jira.client.JIRA( options=jira_options, basic_auth=jira_auth )
    sprintly_client   = sprintly.Client( sprintly_auth )

    jira_projects     = map_with( jira_client.projects(),     get_key=lambda x:x.raw['name'] )
    sprintly_products = map_with( sprintly_client.products(), get_key=lambda x:x.raw['name'] )

    auto_map = guess_mapping( jira_projects, sprintly_products )     
    for (jir_proj,spr_prod) in auto_map.iteritems():
        if spr_prod:
            print "JIRA proj: %s mapped to %s"%(jir_proj,spr_prod)
        else:
            print "JIRA proj: %s not mapped. Select Sprintly Product to map to?"%(jir_proj)
    
    prod_map = dict(auto_map) #FIXME
    for (jir_proj_name,spr_prod_name) in prod_map.iteritems():

        jproj = jira_projects[jir_proj_name]
        if spr_prod:
            print "JIRA proj: %s mapped to %s"%(jir_proj_name,spr_prod_name)
            print "Using existing sprintly product"%(spr_prod_name)
        else:
            print "JIRA proj: %s not mapped. Select Sprintly Product to map to?"%(jir_proj_name)
            print "creating sprintly product"
            sprintly_client.create_product(jir_proj_name)
            spr_prod_name = jir_proj_name

        spr_prod = sprintly_client.get_product(spr_prod_name)
        print "Got Sprintly product %s:%s"%(spr_prod.name,spr_prod.id)

        print "Downloading jira items."
        jissues = jira_client.search_issues('project=%s'%jproj.key)
        for jissue in jissues:
            if spr_prod.search_issue('tag=%s'%jissue.key):
                print "Converting issue %s:%s"%(jissue.key,jissue.title)





