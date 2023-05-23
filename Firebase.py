import asyncio
import firebase_admin
from firebase_admin import credentials, initialize_app, storage, firestore
import random
import string

cred = credentials.Certificate('C:\\Users\\HS.Robotics\\Downloads\\liminal-302-cred.json')
initialize_app(cred, {'storageBucket': 'liminal-302.appspot.com'})

bucket = storage.bucket()
async def upload():
    fileName = ("C:\\Users\\HS.Robotics\\Downloads\\SpEnCer.PNG")
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)
    blob.make_public()
    print("your file url", blob.public_url)
asyncio.run(upload())

length = int(input('5'))
characterList = [1,2,3,4,5,6,7,8,9,0]

db.collection('prints').document('test').set({
    u'name': u'Los Angeles',
    u'state': u'CA',
    u'country': u'USA'
})