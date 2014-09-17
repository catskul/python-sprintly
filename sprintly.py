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
            setattr( self, thing, raw_dict[thing] )  

    def __repr__(self):
        return '<%s.%s: name=%s>'%(self.__module__,self.__class__.__name__,self.raw['name'])

    def people(self):
        return self.client.people(self.raw['id'])

    def create_person(self,data):
        return self.client.create_person(self.raw['id'],data)

    def items(self):
        return self.client.items(self.raw['id'])


class Person:
    raw = None
    client = None

    def __init__(self, client, raw_dict):
        self.raw    = raw_dict
        self.client = client
        for thing in self.raw:
            setattr( self, thing, raw_dict[thing] )  

    def __repr__(self):
        return '<%s.%s: email=%s>'%(self.__module__,self.__class__.__name__,self.raw['email'])


class Item:
    raw = None
    client = None

    def __init__(self, client, raw_dict):
        self.raw    = raw_dict
        self.client = client
        for thing in self.raw:
            setattr( self, thing, raw_dict[thing] )  

    def __repr__(self):
        return '<%s.%s: id=%s, title=%s>'%(self.__module__,self.__class__.__name__,self.raw['number'], self.raw['title'])

class Client:
    def __init__(self, basic_auth):
        self.basic_auth = basic_auth
    
    def api_get(self, call, thing_type):
        api_url = SPRINTLY_API_URI + '/' + call
        req = requests.get(api_url, auth=self.basic_auth)
        req.raise_for_status()
       
        response = json.loads(req.content) 
        if type(response) is list:
            return [ thing_type(self, item) for item in response ]
        else:
            return thing_type(self, response);

    def api_post(self, call, thing_type, data):
        api_url = SPRINTLY_API_URI + '/' + call
        req = requests.post(api_url, auth=self.basic_auth, data=data)
        req.raise_for_status()
        
        response = json.loads(req.content)
        if type(response) is list:
            return [ thing_type(self, item) for item in response ]
        else:
            return thing_type(self, response)

    def products(self):
        return self.api_get("products.json",Product)

    def create_product(self, name):
        data = { 'name' : name }
        return self.api_post("products.json",Product,data)

    def items(self, product_id):
        return self.api_get("products/%s/items.json"%product_id,Item)
        
    def people(self, product_id): 
        return self.api_get("products/%s/people.json"%product_id,Person)

    def create_person(self, product_id, data):
        return self.api_post("products/%s/people.json"%product_id,Person,data)

    #def get_spr_user_email_map(self, product):
    #    return { user['email'] : user for user in sprintly_users } 
