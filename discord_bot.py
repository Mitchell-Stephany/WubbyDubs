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
            
            # Determine deal type
            is_arbitrage = deal.get('is_arbitrage', False)
            fallback_mode = deal.get('fallback_mode', False)
            
            if is_arbitrage:
                title = "💰 ARBITRAGE OPPORTUNITY! 💰"
                color = discord.Color.green()
            else:
                title = "🔥 PRICE DROP ALERT! 🔥"
                color = discord.Color.red()
            
            # Create embed
            embed = discord.Embed(
                title=title,
                color=color,
                url=deal.get('url')
            )
            
            embed.add_field(name="Product", value=deal.get('name', 'Unknown'), inline=False)
            embed.add_field(name="Retailer", value=deal.get('retailer', 'Unknown'), inline=True)
            embed.add_field(name="Category", value=deal.get('category', 'Unknown'), inline=True)
            
            # Price information
            original_price = deal.get('original_price', 0)
            new_price = deal.get('new_price', 0)
            drop_percentage = deal.get('drop_percentage', 0)
            
            embed.add_field(
                name="Price Drop",
                value=f"~~${original_price:.2f}~~ → **${new_price:.2f}** ({drop_percentage:.1f}% off)",
                inline=False
            )
            
            # eBay arbitrage info
            ebay_price = deal.get('ebay_price')
            ebay_price_range = deal.get('ebay_price_range')
            potential_profit = deal.get('potential_profit', 0)
            profit_percentage = deal.get('profit_percentage', 0)
            roi = deal.get('roi', 0)
            ebay_confidence = deal.get('ebay_confidence')
            sample_size = deal.get('sample_size')
            
            if ebay_price and not fallback_mode:
                # eBay price info
                ebay_value = f"**${ebay_price:.2f}**"
                if ebay_price_range:
                    ebay_value += f"\nRange: {ebay_price_range}"
                if sample_size:
                    ebay_value += f"\nBased on {sample_size} sold listings"
                if ebay_confidence:
                    confidence_emoji = {'high': '🟢', 'medium': '🟡', 'low': '🟠', 'very_low': '🔴'}.get(ebay_confidence, '⚪')
                    ebay_value += f"\nConfidence: {confidence_emoji} {ebay_confidence}"
                
                embed.add_field(name="eBay Sold Price", value=ebay_value, inline=False)
                
                # Profit info
                if potential_profit > 0:
                    embed.add_field(
                        name="💰 Estimated Profit",
                        value=f"**${potential_profit:.2f}** ({profit_percentage:.1f}% margin)\nROI: {roi:.1f}%",
                        inline=True
                    )
                    # Fees note
                    fees = ebay_price - potential_profit - new_price
                    embed.add_field(
                        name="eBay Fees (est.)",
                        value=f"${fees:.2f}",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="Profit",
                        value=f"-${abs(potential_profit):.2f} (not profitable after fees)",
                        inline=False
                    )
            elif fallback_mode:
                embed.add_field(
                    name="Note",
                    value="⚠️ No eBay data available - price drop only (not arbitrage verified)",
                    inline=False
                )
            
            embed.add_field(name="🛒 Buy Here", value=deal.get('url', 'N/A'), inline=False)
            
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
