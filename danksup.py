from yowsup.layers.protocol_media.protocolentities import \
    RequestUploadIqProtocolEntity, \
    ImageDownloadableMediaMessageProtocolEntity, \
    AudioDownloadableMediaMessageProtocolEntity, \
    VideoDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_media.mediauploader import MediaUploader
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from yowsup.layers.protocol_presence.protocolentities import PresenceProtocolEntity
from yowsup.layers.protocol_profiles.protocolentities import SetStatusIqProtocolEntity
from yowsup.layers.protocol_groups.protocolentities import AddParticipantsIqProtocolEntity, PromoteParticipantsIqProtocolEntity
from yowsup.layers.auth import YowAuthenticationProtocolLayer
from yowsup.common.tools import Jid

from promise import Promise
import sys

class Danksup:
    def __init__(self, layer):
        self.layer = layer

    def setName(self, name):
        self.toLower(PresenceProtocolEntity(name=name))

    def setStatus(self, status):
        return self._sendIq(SetStatusIqProtocolEntity(text=status))

    def kill(self):
        sys.exit(0)

    def send(self, jid, message="", image=None):
        # message = message.encode().decode("latin-1")
        if image:
            return self._sendMedia(jid, image, RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE, message)
        else:
            return self._sendMessage(jid, message)

    def _sendMessage(self, jid, message):
        print("Sending message '{}' to {}".format(message, jid))
        self.toLower(TextMessageProtocolEntity(message, to=jid))
        return Promise.resolve(None)

    def _sendMedia(self, jid, path, mediaType, caption):
        print("Sending media of type {} at '{}' to {} with caption '{}'".format(mediaType, path, jid, caption))
        def uploadIfNotAlready(result):
            if not result.isDuplicate():
                url = result.getUrl()
                offset = result.getResumeOffset()
                return self._uploadMedia(jid, path, mediaType, url, offset).then(lambda resultUrl: (result, resultUrl))
            else:
                return (result, result.getUrl())
        def sendMediaForReal(x):
            result, url = x
            print("Sending for real now")
            ip = result.getIp()
            if mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE:
                entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(path, url, ip, jid, caption = caption)
            elif mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO:
                entity = AudioDownloadableMediaMessageProtocolEntity.fromFilePath(path, url, ip, jid)
            elif mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_VIDEO:
                entity = VideoDownloadableMediaMessageProtocolEntity.fromFilePath(path, url, ip, jid, caption = caption)
            if not entity:
                raise ValueError()
            self.toLower(entity)

        return self._requestUploadMedia(mediaType, path) \
            .then(uploadIfNotAlready) \
            .then(sendMediaForReal)

    def _requestUploadMedia(self, mediaType, path):
        return self._sendIq(RequestUploadIqProtocolEntity(mediaType, filePath=path))

    def _uploadMedia(self, jid, path, mediaType, url, offset):
        def promise(resolve, reject):
            def success(path, jid, resultUrl):
                print("Uploading success")
                resolve(resultUrl)
            def failure(path, jid, uploadUrl):
                print("Uploading failure")
                reject(RuntimeError("Could not upload {} to {}".format(path, uploadUrl)))
            def progress(filePath, jid, url, progress):
                pass
                #print("Progress of filePath {}".format(progress))
            ownJid = self._getOwnJid()
            uploader = MediaUploader(jid, ownJid, path, url, offset, success, failure, progress, async=False)
            print("Uploading")
            uploader.start()

        return Promise(promise)

    def addParticipantsToGroup(self, groupJid, participantJids):
        return self._sendIq(AddParticipantsIqProtocolEntity(groupJid, participantJids))

    def promoteParticipantsInGroup(self, groupJid, participantJids):
        return self._sendIq(PromoteParticipantsIqProtocolEntity(groupJid, participantJids))
    def _getOwnJid(self):
        return self.layer.getLayerInterface(YowAuthenticationProtocolLayer).getUsername(True)


    def _sendIq(self, entity):
        return Promise(lambda resolve, reject:
                self.layer._sendIq(entity, lambda result, _: resolve(result), lambda failure, _: reject(failure)))


    def toLower(self, entity):
        return self.layer.toLower(entity)

class DanksupContext:
    TARGET_WHOLE = "whole"
    TARGET_INDIVIDUAL = "individual"
    def __init__(self, messageEntity, danksup):
        self.danksup = danksup
        self.messageEntity = messageEntity

    def reply(self, message="", image=None, target=None):
        if target == None:
            target = self.TARGET_WHOLE
        if target == self.TARGET_WHOLE:
            jid = self.getFrom()
        elif target == self.TARGET_INDIVIDUAL:
            jid = self.getAuthor()
        jid = Jid.normalize(jid)
        return self.send(jid, message, image)

    def addToGroup(self, groupJid):
        return self.addParticipantsToGroup(groupJid, [self.getAuthor()])

    def promote(self):
        if self.isGroupMessage():
            return self.promoteParticipantsInGroup(self.getFrom(), [self.getAuthor()])
        else:
            return Promise.reject(RuntimeError("DanksupContext.promote() only valid for group messages"))

    def getAuthor(self):
        return self.messageEntity.getAuthor()

    def getFrom(self):
        return self.messageEntity.getFrom()


    def isGroupMessage(self):
        return self.messageEntity.isGroupMessage()

    def __getattr__(self, name):
        return self.danksup.__getattribute__(name)
