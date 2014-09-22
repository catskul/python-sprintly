import json
import requests
import sys

SPRINTLY_URI      = 'https://sprint.ly'
SPRINTLY_API_PATH = '/api'
SPRINTLY_API_URI  = SPRINTLY_URI + SPRINTLY_API_PATH

class ApiThing:
    def __repr__(self):
        origin = '%s.%s'%(self.__module__,self.__class__.__name__)
        values = ' '.join( [ '%s=[%s]'%(name,getattr(self,name)) for name in self.repr_list ] )
        return '<%s: %s>'%(origin,values)
    
    def __hash__(self):
        return hash( tuple( [ getattr( self, part ) for part in self.hash_parts ] ) )
    
    def __eq__(self,other):
        return self.__hash__() == other.__hash__()


class Product(ApiThing):
    def __init__(self, client, raw_dict):
        self.raw    = raw_dict
        self.client = client
        self.repr_list = ['name','id']
        self.hash_parts = ['id']
        for thing in self.raw:
            setattr( self, thing, raw_dict[thing] )  

    def people(self):
        return self.client.people(self.raw['id'])

    def create_person(self,data):
        return self.client.create_person(self.raw['id'],data)

    def items(self):
        return self.client.items(self.raw['id'])

    def create_item(self,data,client=None):
        client = client or self.client
        return client.create_item(self.raw['id'],data)


class Person(ApiThing):
    def __init__(self, client, raw_dict):
        self.raw    = raw_dict
        self.client = client
        self.repr_list = ['email','id']
        self.hash_parts = ['id']
        for thing in self.raw:
            setattr( self, thing, raw_dict[thing] )  


class Item(ApiThing):
    def __init__(self, client, raw_dict):
        self.raw    = raw_dict
        self.client = client
        self.repr_list = ['title','number']
        self.hash_parts = ['number']
        for thing in self.raw:
            setattr( self, thing, raw_dict[thing] )  

    def comments(self):
        return self.client.comments(self.product['id'],self.number)

    def create_comment(self,data,client=None):
        client = client or self.client
        return client.create_comment(self.product['id'],self.number,data)


class Comment(ApiThing):
    def __init__(self, client, raw_dict):
        self.raw    = raw_dict
        self.client = client
        self.repr_list = ['id']
        self.hash_parts = ['id']
        for thing in self.raw:
            setattr( self, thing, raw_dict[thing] )  
    

class Client:
    def __init__(self, basic_auth, fake_create=False):
        self.basic_auth = tuple(basic_auth)
        self.fake_create = fake_create
    
    def api_get(self, call, thing_type, params=None):
        api_url = SPRINTLY_API_URI + '/' + call
        req = requests.get(api_url, auth=self.basic_auth, params=params)
        req.raise_for_status()
       
        response = json.loads(req.content) 
        if type(response) is list:
            return [ thing_type(self, item) for item in response ]
        else:
            return thing_type(self, response);

    def api_post(self, call, thing_type, data, fake_data=None):
        api_url = SPRINTLY_API_URI + '/' + call
        
        if self.fake_create:
            print "faking post request to [%s] and reflecting data back" % api_url
            response = data
            if fake_data:
                response.update( fake_data )
            #print "reflected data: %s" % response
        else:
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
        params = {
            'status' : 'backlog,in-progress,completed,accepted',
            'limit'  : 100,
            'offset' : 0,
        }
        data = []
        count = 1
        while count > 0:
            res = self.api_get("products/%s/items.json"%product_id,Item,params=params)
            params['offset'] += params['limit']
            data += res
            count = len( res )

        return data
        
    def create_item(self, product_id, data):
        fake_data = { 
            'number' : -1,
            'product' : { 'id' : product_id }
        }
        return self.api_post("products/%s/items.json"%product_id,Item,data,fake_data=fake_data)

    def comments(self,product_id, item_number):
        if item_number == -1 or item_number == -1:
            return []
        else:
            return self.api_get("products/%s/items/%s/comments.json"%(product_id,item_number),Comment)

    def create_comment(self,product_id, item_number, data):
        return self.api_post("products/%s/items/%s/comments.json"%(product_id,item_number),Comment,data)

    def people(self, product_id): 
        return self.api_get("products/%s/people.json"%product_id,Person)

    def create_person(self, product_id, data):
        return self.api_post("products/%s/people.json"%product_id,Person,data)

    def all_people(self,products=None):
        products = products or self.products()
        people = set()
        for product in products:
            people.update( product.people() )

        return people
