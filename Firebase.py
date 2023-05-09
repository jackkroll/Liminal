import asyncio
from firebase_admin import credentials, initialize_app, storage

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
