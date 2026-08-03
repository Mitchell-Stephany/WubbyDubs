import asyncio
import logging
import threading
from typing import Dict, Optional

import discord

from exceptions import ConfigError, NotificationError

logger = logging.getLogger(__name__)

class DiscordBot(discord.Client):
    """Discord bot for sending deal notifications"""
    
    def __init__(self, config):
        intents = discord.Intents.default()
        intents.message_content = False  # Disable privileged intent
        super().__init__(intents=intents)
        
        self.config = config
        self.channel_id = config.DISCORD_CHANNEL_ID
        # The bot runs on its own event loop in a worker thread, so readiness has to be
        # signalled with a thread-safe primitive rather than an asyncio.Event.
        self.ready_event = threading.Event()
        self.startup_error: Optional[Exception] = None
        self.bot_loop: Optional[asyncio.AbstractEventLoop] = None
    
    async def on_ready(self):
        logger.info('%s has connected to Discord!', self.user)
        self.ready_event.set()

    def _resolve_channel(self):
        """Return the configured channel, raising NotificationError when unusable."""
        if not self.channel_id:
            raise NotificationError("DISCORD_CHANNEL_ID is not configured")

        channel = self.get_channel(self.channel_id)
        if channel is None:
            raise NotificationError(
                f"Discord channel {self.channel_id} is not visible to this bot"
            )
        return channel

    async def _send(self, embed: discord.Embed, description: str):
        channel = self._resolve_channel()
        try:
            await channel.send(embed=embed)
        except discord.DiscordException as exc:
            raise NotificationError(f"Failed to send {description} to Discord: {exc}") from exc

    async def send_deal_notification(self, deal: Dict):
        """Send a formatted deal notification to Discord"""
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

        await self._send(embed, f"deal notification for {deal.get('name')}")
        logger.info("Sent deal notification for %s", deal.get('name'))

    async def send_summary(self, deals: list):
        """Send a summary of multiple deals"""
        if not deals:
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

        await self._send(embed, "deal summary")

    async def send_error_notification(self, error_message: str):
        """Send an error notification"""
        embed = discord.Embed(
            title="⚠️ System Error",
            description=error_message,
            color=discord.Color.orange()
        )

        await self._send(embed, "error notification")

    async def start_bot(self):
        """Start the Discord bot"""
        if not self.config.DISCORD_BOT_TOKEN:
            raise ConfigError("DISCORD_BOT_TOKEN is not configured")

        self.bot_loop = asyncio.get_running_loop()
        try:
            await self.start(self.config.DISCORD_BOT_TOKEN)
        except Exception as exc:
            # Record the failure so waiters are released instead of blocking forever.
            self.startup_error = exc
            self.ready_event.set()
            raise

    async def wait_until_ready(self, timeout: float = None):
        """Wait until the bot is connected, raising NotificationError if it never connects."""
        timeout = timeout if timeout is not None else getattr(
            self.config, 'DISCORD_READY_TIMEOUT_SECONDS', 30.0
        )
        loop = asyncio.get_running_loop()
        connected = await loop.run_in_executor(None, self.ready_event.wait, timeout)

        if self.startup_error is not None:
            raise NotificationError(
                f"Discord bot failed to start: {self.startup_error}"
            ) from self.startup_error

        if not connected:
            raise NotificationError(
                f"Discord bot did not become ready within {timeout} seconds"
            )

    async def deliver_deal(self, deal: Dict):
        """Send a deal from another event loop, e.g. the scheduler's."""
        if self.bot_loop is None:
            raise NotificationError("Discord bot is not running")

        future = asyncio.run_coroutine_threadsafe(
            self.send_deal_notification(deal), self.bot_loop
        )
        await asyncio.wrap_future(future)
