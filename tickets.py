# importing the required modules
import disnake
from disnake.ext import commands
import os
import asyncio
import time

class TicketButton(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.persistents_views_added = False
        self.tickets = []
        self.users = {}

    @disnake.ui.button(style=disnake.ButtonStyle.blurple, label="Open ticket", custom_id="create", emoji="➕")
    async def create(self, button: disnake.ui.Button, inter: disnake.ApplicationCommandInteraction):
        if inter.author.id in self.users and time.time() - self.users[inter.author.id] < 3600:
            remaining_time = int((self.users[inter.author.id] + 3600 - time.time()) // 60)
            return await inter.response.send_message(
                f"The time to create a new ticket has not yet come. New ticket will be available through {remaining_time} minutes.",
                ephemeral=True)
        else:
            self.users[inter.author.id] = time.time()

        # Creates a ticket category if it doesn't exist
        if not disnake.utils.get(inter.guild.categories, name="Tickets"):
            await inter.guild.create_category("Tickets")

        # Creates the ticket channel
        channel = await inter.guild.create_text_channel(
            name=f"ticket-{inter.author.name}",
            category=disnake.utils.get(inter.guild.categories, name="Tickets"),
            topic=f"Ticket created by {inter.author.name} | {inter.author.id} Creation time: {inter.created_at}",
            reason=f"Reason {inter.author.name}",
        )
        self.tickets.append(inter.author.id)
        self.users[inter.author.id] = time.time()  # record time of ticket creation
        # Sets the permissions for the ticket channel
        await channel.set_permissions(inter.author, send_messages=True, read_messages=True,
                                      read_message_history=True, attach_files=True, embed_links=True,
                                      add_reactions=True, external_emojis=True, use_external_emojis=True,
                                      use_slash_commands=True)
        await channel.set_permissions(inter.guild.default_role, send_messages=False, read_messages=False)

        # Sends a message to the ticket channel
        view = Button()
        embed = disnake.Embed(colour=0x2B2D31)
        embed.set_image(url='https://cdn.discordapp.com/attachments/1087624157333819452/1098554244287701022/ticket_leon.png')
        embed2 = disnake.Embed(title=f'You are in {inter.guild.name}, how can we help you?',
                               description=f'Thank you for your cooperation with the {inter.guild.name}\' admins. Please list your problem or problems while you wait for the staff to come help you today!',
                               colour=0x2B2D31)
        embed2.set_footer(text=f'Command used by {inter.author}', icon_url=inter.author.avatar.url)
        embed2.set_thumbnail(url=inter.author.avatar.url)
        embed2.set_image(
            url='https://cdn.discordapp.com/attachments/1006260133162123338/1089553149943087185/space.png')
        message = await channel.send(embeds=[embed, embed2], view=view)
        await message.pin()
        await channel.send(f'{inter.author.mention}', delete_after=0.1)

        # Sends a message to the user
        embed = disnake.Embed(title='✅ Ticket create',
                              description=f"Your ticket at the {channel.mention} \n Please go to your ticket and list your problem(s)",
                              color=0x2B2D31)
        embed.set_footer(text=f'Command used by {inter.author}', icon_url=inter.author.avatar.url)
        embed.set_thumbnail(url=inter.author.avatar.url)
        await inter.response.send_message(embed=embed, ephemeral=True)



class Button2(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(style=disnake.ButtonStyle.gray, label="Sure", custom_id="close", emoji="✔")
    async def close(self, button: disnake.ui.Button, inter: disnake.ApplicationCommandInteraction):
        channel = disnake.utils.get(inter.guild.channels, name=f"ticket-{inter.author.name}")
        transcript_channel = disnake.utils.get(inter.guild.channels, name="transcript")
        if not transcript_channel:
            category = disnake.utils.get(inter.guild.categories, name="Tickets")
            if not category:
                category = await inter.guild.create_category("Tickets")
            transcript_channel = await inter.guild.create_text_channel("transcript", category=category)
            overwrite = disnake.PermissionOverwrite()
            overwrite.read_messages = False
            await transcript_channel.set_permissions(inter.guild.default_role, overwrite=overwrite)
        if inter.channel.name.startswith("ticket-"):
            messages = []
            async for message in inter.channel.history(limit=None):
                if message.author.id == inter.guild.me.id:
                    continue
                reply = ''
                if message.reactions:
                    reply = f"(Reacted to by {[str(r.users) for r in message.reactions][0]})"
                messages.append(f"{message.author} ({message.author.id}): {message.content} {reply}")
            messages = messages[::-1]
            transcript_file_name = f"transcript-ticket-{inter.author.name}.txt"
            with open(transcript_file_name, "w") as f:
                f.write("\n".join(messages))
            await transcript_channel.send(file=disnake.File(transcript_file_name))
            await inter.channel.delete()
            os.remove(transcript_file_name)
        if inter.author.id in self.tickets:
            self.tickets.remove(inter.author.id)
        else:
            await inter.response.send_message("You do not have an open ticket.")

        await inter.response.defer()

class Button(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(style=disnake.ButtonStyle.gray, label="Close ticket", custom_id="sure", emoji="❌")
    async def sure(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        view = Button2()
        embed = disnake.Embed(title='❓ Are you sure about this?', colour=0x2B2D31)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.persistents_views_added = False
        self.tickets = []
        self.users = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Loaded Cog Tickets')

    @commands.Cog.listener()
    async def on_connect(self):
        if self.persistents_views_added:
            return

        self.bot.add_view(Button())
        self.bot.add_view(TicketButton())
        self.persistents_views_added = True

    # Slash command for tickets which has options of opening a ticket, closing a ticket, and deleting a ticket

    @commands.slash_command(
        name="setup",
        description="Setup tickets menu")
    async def tickets_ebmed(self, ctx):
        view = TicketButton()
        embed = disnake.Embed(title="", colour=0x2B2D31)
        embed.set_image(url='https://cdn.discordapp.com/attachments/1087624157333819452/1098554160519057468/tickets_leon.png')
        embed2 = disnake.Embed(title="Tickets 📮",description="If you have a question for the administration; You found a bug; Proposal for a technical plan; You want to suggest something => Open a ticket" , colour=0x2B2D31)
        embed2.set_image(url='https://cdn.discordapp.com/attachments/1006260133162123338/1089553149943087185/space.png')
        await ctx.channel.send(embeds=[embed, embed2], view=view)


    @commands.slash_command()
    async def ticket(
            self,
            inter: disnake.ApplicationCommandInteraction,
            action: str = commands.Param(choices=["open", "close", "add", "remove"]),
            user: disnake.User = commands.Param(None, description="The user you want to add")
    ):
        try:
            # If the user selects open, it will create a ticket
            if action == "open":
                # Check if user has already created a ticket within the last hour
                if inter.author.id in self.users and time.time() - self.users[inter.author.id] < 3600:
                    remaining_time = int((self.users[inter.author.id] + 3600 - time.time()) // 60)
                    return await inter.response.send_message(
                        f"The time to create a new ticket has not yet come. New ticket will be available through {remaining_time} minutes.",
                        ephemeral=True)
                else:
                    self.users[inter.author.id] = time.time()

                # Creates a ticket category if it doesn't exist
                if not disnake.utils.get(inter.guild.categories, name="Tickets"):
                    await inter.guild.create_category("Tickets")

                # Creates the ticket channel
                channel = await inter.guild.create_text_channel(
                    name=f"ticket-{inter.author.name}",
                    category=disnake.utils.get(inter.guild.categories, name="Tickets"),
                    topic=f"Ticket created by {inter.author.name} | {inter.author.id} Creation time: {inter.created_at}",
                    reason=f"Reason {inter.author.name}",
                )
                self.tickets.append(inter.author.id)
                self.users[inter.author.id] = time.time()  # record time of ticket creation
                # Sets the permissions for the ticket channel
                await channel.set_permissions(inter.author, send_messages=True, read_messages=True,
                                              read_message_history=True, attach_files=True, embed_links=True,
                                              add_reactions=True, external_emojis=True, use_external_emojis=True,
                                              use_slash_commands=True)
                await channel.set_permissions(inter.guild.default_role, send_messages=False, read_messages=False)

                # Sends a message to the ticket channel
                view = Button()
                embed = disnake.Embed(colour=0x2B2D31)
                embed.set_image(url='https://cdn.discordapp.com/attachments/1087624157333819452/1098554244287701022/ticket_leon.png')
                embed2 = disnake.Embed(title=f'You are in {inter.guild.name}, how can we help you?',
                                       description=f'Thank you for your cooperation with the {inter.guild.name}\' admins. Please list your problem or problems while you wait for the staff to come help you today!',
                                       colour=0x2B2D31)
                embed2.set_footer(text=f'Command used by {inter.author}', icon_url=inter.author.avatar.url)
                embed2.set_thumbnail(url=inter.author.avatar.url)
                embed2.set_image(
                    url='https://cdn.discordapp.com/attachments/1006260133162123338/1089553149943087185/space.png')
                message = await channel.send(embeds=[embed, embed2], view=view)
                await message.pin()
                await channel.send(f'{inter.author.mention}', delete_after=0.1)
                await asyncio.sleep(3)  # Wait for 3 seconds
                confirmation_message = await inter.channel.send("Сообщение закреплено!",
                                                              delete_after=5)  # Confirm pinning and delete after 5 seconds
                await asyncio.sleep(5)  # Wait for 5 seconds
                await confirmation_message.delete()  # Delete the confirmation message
                await inter.channel.history(limit=1).flatten()[0].delete()

                # Sends a message to the user
                embed = disnake.Embed(title='✅ Ticket create',
                                      description=f"Your ticket at the {channel.mention} \n Please go to your ticket and list your problem(s)",
                                      color=0x2B2D31)
                embed.set_footer(text=f'Command used by {inter.author}', icon_url=inter.author.avatar.url)
                embed.set_thumbnail(url=inter.author.avatar.url)
                await inter.response.send_message(embed=embed, ephemeral=True)

            # If the user selects close, it will close the ticket
            elif action == "close":
                async def close_ticket():
                    channel = disnake.utils.get(inter.guild.channels, name=f"ticket-{inter.author.name}")
                    transcript_channel = disnake.utils.get(inter.guild.channels, name="transcript")
                    if not transcript_channel:
                        category = disnake.utils.get(inter.guild.categories, name="Tickets")
                        if not category:
                            category = await inter.guild.create_category("Tickets")
                        transcript_channel = await inter.guild.create_text_channel("transcript", category=category)
                        overwrite = disnake.PermissionOverwrite()
                        overwrite.read_messages = False
                        await transcript_channel.set_permissions(inter.guild.default_role, overwrite=overwrite)
                    if inter.channel.name.startswith("ticket-"):
                        messages = []
                        async for message in inter.channel.history(limit=None):
                            if message.author.id == inter.guild.me.id:
                                continue
                            reply = ''
                            if message.reactions:
                                reply = f"(Reacted to by {[str(r.users) for r in message.reactions][0]})"
                            messages.append(f"{message.author} ({message.author.id}): {message.content} {reply}")
                        messages = messages[::-1]
                        transcript_file_name = f"transcript-ticket-{inter.author.name}.txt"
                        with open(transcript_file_name, "w") as f:
                            f.write("\n".join(messages))
                        await transcript_channel.send(file=disnake.File(transcript_file_name))
                        await inter.channel.delete()
                        os.remove(transcript_file_name)
                    if inter.author.id in self.tickets:
                        self.tickets.remove(inter.author.id)
                    else:
                        await inter.response.send_message("You do not have an open ticket.")

                await inter.response.defer()
                asyncio.create_task(close_ticket())

            # If the user selects add, it will add a user to the ticket Ex: /ticket action:add user:Person0z
            elif action == "add":
                channel = disnake.utils.get(
                    inter.guild.channels, name=f"ticket-{inter.author.name}")
                if inter.channel.name.startswith("ticket-"):
                    await channel.set_permissions(inter.user, send_messages=True, read_messages=True)
                    await inter.response.send_message(f"{user.mention} was add to ticket.")
                else:
                    await inter.response.send_message("You do not have an open ticket.")

            # If the user selects remove, it will remove a user from the ticket Ex: /ticket action:remove user:Person0z
            elif action == "remove":
                if inter.channel.name.startswith("ticket-"):
                    await inter.channel.set_permissions(user, send_messages=False, read_messages=False)
                    await inter.response.send_message(f"{user.mention} was remove from ticket.")
                else:
                    await inter.response.send_message("You do not have an open ticket.")

        except Exception as e:
            print(f'Error in ticket: {e}')



def setup(bot):
    bot.add_cog(tickets(bot))