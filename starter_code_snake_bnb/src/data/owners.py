import mongoengine
import datetime

class Owner(mongoengine.Document):
    registered_date = mongoengine.DateTimeField(default=datetime.datetime.now)
    name = mongoengine.StringField(required=True)
    email = mongoengine.StringField(required=True)
    
    snake_ids = mongoengine.ListField(mongoengine.ObjectIdField())
    cage_ids = mongoengine.ListField(mongoengine.ObjectIdField())
    
    meta = {
		'db_alias': 'core',
		'collection': 'owners'
	}
