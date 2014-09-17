import json
import requests
import sys

SPRINTLY_URI      = 'https://sprint.ly'
SPRINTLY_API_PATH = '/api'
SPRINTLY_API_URI  = SPRINTLY_URI + SPRINTLY_API_PATH



class Product:
    raw = None
    client = None
    repr_list = []

    def __init__(self, client, raw_dict):
        self.raw    = raw_dict
        self.client = client
        self.repr_list = ['name']
        for thing in self.raw:
            setattr( self, thing, lambda : raw_dict[thing] )  

    def __repr__(self):
        return '<%s.%s: name=%s>'%(self.__module__,self.__class__.__name__,self.raw['name'])

    def people(self):
        return self.client.people(self.raw['id'])

    def items(self):
        return self.client.items(self.raw['id'])


class Person:
    raw = None
    client = None

    def __init__(self, client, raw_dict):
        self.raw    = raw_dict
        self.client = client

    def __repr__(self):
        return '<%s.%s: name=%s>'%(self.__module__,self.__class__.__name__,self.raw['name'])


class Item:
    raw = None
    client = None

    def __init__(self, client, raw_dict):
        self.raw    = raw_dict
        self.client = client

    def __repr__(self):
        return '<%s.%s: id=%s>'%(self.__module__,self.__class__.__name__,self.raw['id'])

class Client:
    def __init__(self, basic_auth):
        self.basic_auth = basic_auth
    
    def api_call(self, call, thing_type):
        api_call = SPRINTLY_API_URI + '/' + call
        req = requests.get(api_call, auth=self.basic_auth)
        req.raise_for_status()
        
        return [ thing_type(self, item) for item in json.loads(req.content) ]

    def products(self):
        return self.api_call("products.json",Product)

    def items(self, product_id):
        return self.api_call("%s/items.json"%product_id,Item)
        
    def people(self, product_id): 
        return self.api_call("%s/people.json"%product_id,Person)

    #def get_spr_user_email_map(self, product):
    #    return { user['email'] : user for user in sprintly_users } 
