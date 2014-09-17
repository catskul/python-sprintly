import sys

def get_or_create_class( module, class_name ):
    class_type = getattr( module, class_name, None )
    
    if not class_type:
        class_type = type( class_name,(object,), {} )
        setattr( module, class_name, class_type )
    
    return class_type




def objectify_contents( contents ):
    the_type = type(contents)

    if the_type is list or the_type is tuple:
        thing_list = []
        for thing in contents:
            thing_list.append( objectify( thing ) )
        value = the_type( thing_list )
    elif the_type is dict:
        thing_list = []
        for key in contents

    return value


def set_or_graft( obj, content ):
    if type(content) not in (dict,tuple,list):
        obj = content
    else
        if type(content)
            


def pair_to_obj( pair ):
    name     = pair[0]
    contents = pair[1]

    if type(contents) is list:
        new_contents = []
        for thing in contents:
            new_contents.append( dict_to_obj( thing ) )
    elif type(contents) is dict:
        TheClass = get_or_create_class( sys.modules[__name__], name.title() )

        the_obj = TheClass()
        for key in contents:
            if hasattr( the_obj, key ):
                print "Error this class already has this thing"
            else:
                value = dict_to_obj( key, contents )
                setattr( the_obj, key, value )
    else:
        new_contents = contents

    return new_contents
