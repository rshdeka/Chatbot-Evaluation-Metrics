from datetime import datetime
from typing import List

class Message:
    conversationId: str
    feedback: None
    id: str
    messageId: str
    role: str
    content: str
    date: datetime
    product: str
    plugin: str
    arguments: str
    promptTokens: int
    completionTokens: int
    totalTokens: int

    def __init__(self, conversationId: str, feedback: None, id: str,messageId: str, role: str, content: str, date: datetime,
     product: str, plugin: str, arguments: str, promptTokens: int, completionTokens: int, totalTokens: int) -> None:
        self.conversationId = conversationId
        self.feedback = feedback
        self.id = id
        self.messageId = messageId
        self.role = role
        self.content = content
        self.date = date
        self.product = product
        self.plugin = plugin
        self.arguments = arguments
        self.promptTokens = promptTokens
        self.completionTokens = completionTokens
        self.totalTokens = totalTokens
    
    @staticmethod
    def from_dict(data: dict):
        return Message(
            data.get('conversationId'),
            data.get('feedback'),
            data.get('id'),
            data.get('messageId'),
            data.get('role'),
            data.get('content'),
            data.get('date'),
            data.get('product'),
            data.get('plugin'),
            data.get('arguments'),
            data.get('promptTokens'),
            data.get('completionTokens'),
            data.get('totalTokens')
        )

class Conversation:
    id: str
    type: str
    createdAt: datetime
    updatedAt: datetime
    userId: str
    title: str
    channelId: str
    isEvaluated: bool
    messages: List[Message]   

    def __init__(self, id: str, type: str, createdAt: datetime, updatedAt: datetime, userId: str, title: str, channelId: str,isEvaluated: bool , messages: List[Message]) -> None:
        self.id = id
        self.type = type
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.userId = userId
        self.title = title
        self.channelId = channelId
        self.isEvaluated = isEvaluated
        self.messages = messages
       
    @staticmethod
    def from_dict(data: dict):
        return Conversation(
            data.get('id'),
            data.get('type'),
            data.get('createdAt'),
            data.get('updatedAt'),
            data.get('userId'),
            data.get('title'),
            data.get('channelId'),
            data.get('isEvaluated',""),
            data.get('messages')
        )

        @staticmethod
        def to_json(self):
            return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)