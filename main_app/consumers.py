import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .models import Room, Message  # new import


class ChatConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None  # new

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.room = Room.objects.get(name=self.room_name)
        self.user = self.scope['user']  # new

        # connection has to be accepted
        self.accept()

        # join the room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )

        self.send(json.dumps({
            'type': 'user_list',
            'users': [user.username for user in self.room.online.all()],
        }))

        if self.user.is_authenticated:
        # send the join event to the room
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_join',
                    'user': self.user.username,
                }
            )
            self.room.online.add(self.user)

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name,
        )
        
        if self.user.is_authenticated:
            # send the leave event to the room
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'user': self.user.username,
                }
            )
            self.room.online.remove(self.user)

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if not self.user.is_authenticated:  # new
            return                          # new

        # send chat message event to the room
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'user': self.user.username,  # new
                'message': message,
            }
        )
        Message.objects.create(user=self.user, room=self.room, content=message)  # new

    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

    def user_join(self, event):
        self.send(text_data=json.dumps(event))

    def user_leave(self, event):
        self.send(text_data=json.dumps(event))