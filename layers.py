from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from yowsup.common.tools import Jid

from yowsup.layers.protocol_media.protocolentities import RequestUploadIqProtocolEntity

from threading import Event

from dankbot.bot import DankBot
from dankbot.danksup import Danksup, DanksupContext

class BotLayer(YowInterfaceLayer):
    def __init__(self):
        self.danksup = Danksup(self)
        self.dankbot = DankBot()
        super().__init__()

    @ProtocolEntityCallback("success")
    def onSuccess(self, success):
        print("Connected")
        self.danksup.setName("DankBot")

    @ProtocolEntityCallback("notification")
    def onNotification(self, notification):
        self.toLower(notification.ack())

    @ProtocolEntityCallback("failure")
    def onFailure(self, entity):
        print("Failure")

    @ProtocolEntityCallback("message")
    def onMessage(self, message):
        self.toLower(message.ack(True))
        if message.getType() == "text":
            ctxt = DanksupContext(message, self.danksup)
            body = message.getBody()
            if len(body) > 0 and body[0] == '/':
                self.dankbot.process(ctxt, body[1:])

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, receipt):
        print("acking", receipt)
        self.toLower(receipt.ack())

    @ProtocolEntityCallback("iq")
    def onIq(self, entity):
        print(entity)
