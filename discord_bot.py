import discord
from discord.ext import commands
from typing import Dict
import asyncio

class DiscordBot(discord.Client):
    """Discord bot for sending deal notifications"""
    
    def __init__(self, config):
        intents = discord.Intents.default()
        intents.message_content = False  # Disable privileged intent
        super().__init__(intents=intents)
        
        self.config = config
        self.channel_id = config.DISCORD_CHANNEL_ID
        self.ready_event = asyncio.Event()
    
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        self.ready_event.set()
    
    async def send_deal_notification(self, deal: Dict):
        """Send a formatted deal notification to Discord"""
        if not self.channel_id:
            print("No Discord channel ID configured")
            return
        
        try:
            channel = self.get_channel(self.channel_id)
            if not channel:
                print(f"Could not find channel with ID {self.channel_id}")
                return
            
            # Create embed for better formatting
            embed = discord.Embed(
                title="🔥 HOT DEAL FOUND! 🔥",
                color=discord.Color.red(),
                url=deal.get('url')
            )
            
            embed.add_field(name="Product", value=deal.get('name', 'Unknown'), inline=False)
            embed.add_field(name="Retailer", value=deal.get('retailer', 'Unknown').capitalize(), inline=True)
            embed.add_field(name="Category", value=deal.get('category', 'Unknown'), inline=True)
            
            # Price information
            original_price = deal.get('original_price', 0)
            new_price = deal.get('new_price', 0)
            drop_percentage = deal.get('drop_percentage', 0)
            
            embed.add_field(
                name="Price Drop",
                value=f"${original_price:.2f} → ${new_price:.2f} ({drop_percentage:.1f}%)",
                inline=False
            )
            
            # eBay comparison
            ebay_price = deal.get('ebay_price', 0)
            fallback_mode = deal.get('fallback_mode', False)
            
            if ebay_price and not fallback_mode:
                embed.add_field(name="eBay Price", value=f"${ebay_price:.2f}", inline=True)
                
                potential_profit = deal.get('potential_profit', 0)
                profit_percentage = deal.get('profit_percentage', 0)
                
                embed.add_field(
                    name="Potential Profit",
                    value=f"${potential_profit:.2f} ({profit_percentage:.1f}%)",
                    inline=True
                )
            
            if fallback_mode:
                embed.add_field(
                    name="Note",
                    value="Price drop detected (eBay comparison unavailable)",
                    inline=False
                )
            
            embed.add_field(name="Link", value=deal.get('url', 'N/A'), inline=False)
            
            # Add timestamp
            embed.set_footer(text=f"Found at {deal.get('timestamp', 'Unknown')}")
            
            await channel.send(embed=embed)
            print(f"Sent deal notification for {deal.get('name')}")
            
        except Exception as e:
            print(f"Error sending Discord notification: {e}")
    
    async def send_summary(self, deals: list):
        """Send a summary of multiple deals"""
        if not self.channel_id or not deals:
            return
        
        try:
            channel = self.get_channel(self.channel_id)
            if not channel:
                return
            
            embed = discord.Embed(
                title=f"📊 Deal Summary - {len(deals)} New Deals",
                color=discord.Color.blue()
            )
            
            for i, deal in enumerate(deals[:10], 1):  # Limit to 10 deals
                profit = deal.get('potential_profit', 0)
                drop = deal.get('drop_percentage', 0)
                embed.add_field(
                    name=f"{i}. {deal.get('name', 'Unknown')[:30]}",
                    value=f"Drop: {drop:.1f}% | Profit: ${profit:.2f}",
                    inline=False
                )
            
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error sending summary: {e}")
    
    async def send_error_notification(self, error_message: str):
        """Send an error notification"""
        if not self.channel_id:
            return
        
        try:
            channel = self.get_channel(self.channel_id)
            if not channel:
                return
            
            embed = discord.Embed(
                title="⚠️ System Error",
                description=error_message,
                color=discord.Color.orange()
            )
            
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error sending error notification: {e}")
    
    async def start_bot(self):
        """Start the Discord bot"""
        if not self.config.DISCORD_BOT_TOKEN:
            print("No Discord bot token configured")
            return
        
        await self.start(self.config.DISCORD_BOT_TOKEN)
    
    async def wait_until_ready(self):
        """Wait until bot is ready"""
        await self.ready_event.wait()
