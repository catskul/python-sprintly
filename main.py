import requests
import json


***REMOVED***
JIRA_API_PATH     = '/rest/api/2'
JIRA_API_URI      = JIRA_URI + JIRA_API_PATH
SPRINTLY_URI      = 'https://sprint.ly'
SPRINTLY_API_PATH = '/api'
SPRINTLY_API_URI  = SPRINTLY_URI + SPRINTLY_API_PATH

***REMOVED***


def get_jir_user_email_map( project, auth ):
    api_call = JIRA_API_URI + '/user/permission/search?permissions=COMMENT_ISSUE&projectKey=%s&username='%project
    req = requests.get( api_call, auth=auth )
    req.raise_for_status()
    
    jira_users = json.loads(req.content)
    return { user['emailAddress'] : user for user in jira_users }


def get_spr_user_email_map( product, auth ):
    api_call = SPRINTLY_API_URI + "/%s/people.json"%product 
    req = requests.get( api_call, auth=auth )
    req.raise_for_status()

    sprintly_users = json.loads(req.content)
    return { user['email'] : user for user in sprintly_users } 
    

def map_users_spr_to_jir( sprintly_map, jira_map ):
    return { user['id'] : jira_map[user['email']]['name'] for (key,user) in sprintly_map.iteritems() if jira_map.has_key(user['email']) }    


#def do_user_mapping( sprintly_auth, jira_auth ):
#    
#    sprintly_map = get_sprintly_user_email_dict_for( product, sprintly_auth )
#    jira_map     = get_jira_user_email_dict_for( project, jira_auth )
#    return map_users_spr_to_jira


def get_jira_projects( auth ):
    api_call = JIRA_API_URI + '/user/permission/search?permissions=COMMENT_ISSUE&projectKey=%s&username='%(project)



def import_jira_to_sprintly():
    jira_projects     = get_jira_projects( auth )
    sprintly_products = get_sprintly_products( auth )
     
    jir_to_spr_prod_map
     
    for project in jira_projects:
        { distance.nlevenshtein( project['name'] ) : product for product in sprintly_products }

    get_jira_user_email_dict_for
    pass   
