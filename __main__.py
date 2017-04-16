from yowsup.layers import YowParallelLayer
from yowsup.layers.axolotl.props import PROP_IDENTITY_AUTOTRUST
from yowsup.layers.auth import YowAuthenticationProtocolLayer, AuthError
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers.coder import YowCoderLayer
from yowsup.layers import YowLayerEvent
from yowsup.stacks import YowStack, YowStackBuilder
from yowsup.common import YowConstants
from yowsup.stacks import YowStack
from yowsup.env import YowsupEnv

from dankbot.layers import BotLayer

from dankbot.danksup import Danksup, DanksupContext
from dankbot.bot import DankBot

from os.path import expanduser

def getCredentials():
    with open(expanduser("~/.config/whatsapp"), 'r') as f:
        fields = dict(line.strip().split('=',1) for line in f.readlines())
    return fields['phone'], fields['password']

def main():
    botLayer = BotLayer()
    stack = YowStackBuilder.getDefaultStack(botLayer,
                                            axolotl=True,
                                            groups=True,
                                            media=True,
                                            privacy=True,
                                            profiles=True)
    stack.setProp(YowNetworkLayer.PROP_ENDPOINT, YowConstants.ENDPOINTS[0])
    stack.setProp(YowCoderLayer.PROP_DOMAIN, YowConstants.DOMAIN)
    stack.setProp(YowCoderLayer.PROP_RESOURCE, YowsupEnv.getCurrent().getResource())
    stack.setCredentials(getCredentials())
    stack.setProp(PROP_IDENTITY_AUTOTRUST, True)


    stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
    stack.loop()

if __name__==  "__main__":
    main()
