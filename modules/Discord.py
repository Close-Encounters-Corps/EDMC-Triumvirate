
# -*- coding: utf-8 -*- 


from discord_webhook import    DiscordWebhook, DiscordEmbed

class webhook():
    def __init__(SQID):
        if SQID != "":
            this.SQID=SQID
        else: SQID="None"




        def Send(self,cmdr,SQID,action,params):    #
            '''
            cmdr- User of Plugin
            action- name of webhook
            params - dist of parametrs
            '''
            self.webhook = DiscordWebhook(url='https://discordapp.com/api/webhooks/599240932663230505/HGgJcfmqPwLvDXh4z6mZ1gBUq7TQkBvy4YrvfHsPjeGlgktgma8ZcHXDiG10OgUYKFMu',
                                    username="Test Hook",
                                    content='<@599244131570810902>' )
            self.embed = DiscordEmbed(title='Test', description='This is my first start, boi', color=242424)
            self.embed.set_author(name="KAZ")
            self.embed.set_footer(text='blya')
            self.embed.set_timestamp()
            self.embed.add_embed_field(name='1', value='cto to tam')
            self.embed.add_embed_field(name='Field 2', value='dolor sit')
            self.embed.add_embed_field(name='Field 3', value='amet consetetur')
            self.embed.add_embed_field(name='Field 4', value='sadipscing elitr')
        
            self.webhook.add_embed(self.embed)
            self.webhook.execute()