import json
import requests
import sys

SPRINTLY_URI = 'https://sprint.ly'
SPRINTLY_API_PATH = '/api'
SPRINTLY_API_URI = SPRINTLY_URI + SPRINTLY_API_PATH


def wrap(data, thing_type, client, **kwargs):
    if isinstance(data, list):
        return [thing_type(client, item, **kwargs) for item in data]
    else:
        return thing_type(client, data, **kwargs)


class Account:

    def __init__(self, basic_auth, fake_create=False):
        self.client = Client(basic_auth, fake_create)

    def products(self):
        return wrap(self.client.products(), Product, self.client)

    def all_people(self, products=None):
        products = products or self.products()
        people = set()
        for product in products:
            people.update(product.people())

        return people


class ApiThing:

    def __repr__(self):
        origin = '%s.%s' % (self.__module__, self.__class__.__name__)
        values = ' '.join(['%s=[%s]' % (name, getattr(self, name)) for name in self.repr_list])
        return '<%s: %s>' % (origin, values)

    def __hash__(self):
        return hash(tuple([getattr(self, part) for part in self.hash_parts]))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def update_with(self, data_dict):
        for thing in data_dict:
            setattr(self, thing, data_dict[thing])


class Product(ApiThing):

    def __init__(self, client, raw_dict):
        self.raw = raw_dict
        self.client = client
        self.repr_list = ['name', 'id']
        self.hash_parts = ['id']
        self.update_with(self.raw)

    def people(self):
        return wrap(self.client.people(self.raw['id']), Person, self.client)

    def create_person(self, data):
        return wrap(self.client.create_person(self.raw['id'], data), Person, self.client)

    def items(self, status=None):
        return wrap(self.client.items(self.raw['id'], status), Item, self.client)

    def item(self, item_number):
        return wrap(self.client.item(self.raw['id'], item_number), Item, self.client)

    def create_item(self, data, client=None):
        client = client or self.client
        return wrap(client.create_item(self.raw['id'], data), Item, self.client)


class Person(ApiThing):

    def __init__(self, client, raw_dict):
        self.raw = raw_dict
        self.client = client
        self.repr_list = ['email', 'id']
        self.hash_parts = ['id']
        self.update_with(self.raw)


class Item(ApiThing):

    def __init__(self, client, raw_dict):
        self.raw = raw_dict
        self.client = client
        self.repr_list = ['title', 'number']
        self.hash_parts = ['number']
        self.update_with(self.raw)

    def comments(self):
        return wrap(
            self.client.comments(self.product['id'], self.number),
            Comment, self.client, product_id=self.product['id'], item_number=self.number
        )
    
    def comment(self, id):
        return wrap(
            self.client.comment(self.product['id'], self.number, id),
            Comment, self.client, product_id=self.product['id'], item_number=self.number
        )

    def create_comment(self, data, client=None):
        client = client or self.client
        return wrap(
            client.create_comment(self.product['id'], self.number, data),
            Comment, self.client, product_id=self.product['id'], item_number=self.number
        )

    def save(self):
        fields = [
            'title',
            'who',
            'what',
            'why',
            'description',
            'score',
            'status',
            'assigned_to',
            'tags',
            'parent',
        ]
        if self.type == 'story':
            fields.remove('title')

        fields = set(fields).intersection(set(self.raw))

        data = {field: getattr(self, field) for field in fields}
        for key in data:
            if isinstance(data[key], dict):
                data[key] = data[key]['id']

        return_data = self.client.update_item(self.product['id'], self.number, data)
        self.raw = return_data
        self.update_with(self.raw)
        return self

    def delete(self):
        return self.client.delete_item(self.product['id'], self.number)


class Comment(ApiThing):

    def __init__(self, client, raw_dict, **kwargs):
        self.product_id = kwargs['product_id']
        self.item_number = kwargs['item_number']
        self.raw = raw_dict
        self.client = client
        self.repr_list = ['id']
        self.hash_parts = ['id']
        self.update_with(self.raw)

# Doesn't currently work in the API
#    def save(self):
#        fields = [ 'body' ]
#        data = { field : getattr( self, field ) for field in fields }
#        return_data = self.client.update_comment( self.product_id, self.item_number, self.id, data )
#        self.raw = return_data
#        self.update_with( self.raw )
#        return self


class Client:

    def __init__(self, basic_auth, fake_create=False):
        self.basic_auth = tuple(basic_auth)
        self.fake_create = fake_create

    def api_get(self, call, params=None):
        api_url = SPRINTLY_API_URI + '/' + call
        req = requests.get(api_url, auth=self.basic_auth, params=params)
        req.raise_for_status()

        response = json.loads(req.content)

        return response

    def api_post(self, call, data, fake_data=None):
        api_url = SPRINTLY_API_URI + '/' + call

        if self.fake_create:
            print "faking post request to [%s] and reflecting data back" % api_url
            response = data
            if fake_data:
                response.update(fake_data)
            # print "reflected data: %s" % response
        else:
            req = requests.post(api_url, auth=self.basic_auth, data=data)
            req.raise_for_status()

            response = json.loads(req.content)
        return response

    def api_delete(self, call, params=None):
        api_url = SPRINTLY_API_URI + '/' + call
        req = requests.delete(api_url, auth=self.basic_auth)
        req.raise_for_status()

        response = json.loads(req.content)

        return response

    def products(self):
        return self.api_get("products.json")

    def create_product(self, name):
        data = {'name': name}
        return self.api_post("products.json", data)

    def items(self, product_id, status=None):
        params = {
            'status': 'someday,backlog,in-progress,completed,accepted',
            'limit': 100,
            'offset': 0,
        }
        params['status'] = status or params['status']
        data = []
        count = 1
        while count > 0:
            print "getting items starting at %s" % params['offset']
            res = self.api_get("products/%s/items.json" % product_id, params=params)
            params['offset'] += params['limit']
            data += res
            count = len(res)

        return data

    def item(self, product_id, item_number):
        return self.api_get("products/%s/items/%s.json" % (product_id, item_number))

    def create_item(self, product_id, data):
        fake_data = {
            'number': -1,
            'product': {'id': product_id}
        }
        return self.api_post("products/%s/items.json" % product_id, data, fake_data=fake_data)

    def update_item(self, product_id, item_number, data):
        return self.api_post("products/%s/items/%s.json" % (product_id, item_number), data)

    def delete_item(self, product_id, item_number):
        return self.api_delete("products/%s/items/%s.json" % (product_id, item_number))

    def comments(self, product_id, item_number):
        if item_number == -1 or item_number == -1:
            return []
        else:
            return self.api_get("products/%s/items/%s/comments.json" % (product_id, item_number))
    
    def comment(self, product_id, item_number, comment_id):
        return self.api_get("products/%s/items/%s/comments/%s.json" % (product_id, item_number, comment_id))

    def create_comment(self, product_id, item_number, data):
        return self.api_post("products/%s/items/%s/comments.json" % (product_id, item_number), data)

    def update_comment(self, product_id, item_number, comment_number, data):
        return self.api_post("products/%s/items/%s/comments/%s.json" % (product_id, item_number, comment_number), data)

    def delete_comment(self, product_id, item_number, comment_number):
        return self.api_delete("products/%s/items/%s/comments/%s.json" % (product_id, item_number, comment_number))

    def people(self, product_id):
        return self.api_get("products/%s/people.json" % product_id)

    def create_person(self, product_id, data):
        return self.api_post("products/%s/people.json" % product_id, data)
