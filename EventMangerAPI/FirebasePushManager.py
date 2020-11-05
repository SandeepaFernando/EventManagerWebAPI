import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate('F:\Projects\Eventz\EventManagerWeb\service-account-file.json')
default_app = firebase_admin.initialize_app(cred)
print(default_app.name)

def sendPush(title, msg, registration_token, dataObject=None):
    # See documentation on defining a message payload.
    # message = messaging.MulticastMessage(
    #     notification=messaging.Notification(
    #         title=title,
    #         body=msg
    #     ),
    #     data=dataObject,
    #     tokens=registration_token,
    # )

    message = messaging.MulticastMessage(
        data={
            "data": str(dataObject),
            "title": title,
            "body": msg
        },
        tokens=registration_token,
    )

    # Send a message to the device corresponding to the provided
    # registration token.
    response = messaging.send_multicast(message)
    # Response is a message ID string.
    print('Successfully sent message:', response)