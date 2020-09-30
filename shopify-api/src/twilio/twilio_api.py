from twilio.rest import Client


account_sid = 'AC115b9f3459e887c89d83303a6431b6a4'
auth_token = '64ab795d505c48454c5c61be4c7e14e7'


def create_room(room_name):
    client = Client(account_sid, auth_token)

    room = client.video.rooms.create(
        record_participants_on_connect=True,
        status_callback='http://example.org',
        type='group-small',
        unique_name=room_name
    )
    print(room)
