import pytest

from discord_bot import DiscordBot


class FakeChannel:
    def __init__(self, error=None):
        self.sent = []
        self.error = error

    async def send(self, embed=None, **kwargs):
        if self.error is not None:
            raise self.error
        self.sent.append(embed)


@pytest.fixture
def bot(config):
    return DiscordBot(config)


def use_channel(bot, channel):
    bot.get_channel = lambda channel_id: channel


def field_values(embed):
    return {field.name: field.value for field in embed.fields}


def deal(**overrides):
    payload = {
        'product_id': 'generic_electronics_0',
        'name': 'Wireless Earbuds',
        'retailer': 'target',
        'category': 'electronics',
        'url': 'https://example.com/p/1',
        'original_price': 100.0,
        'new_price': 60.0,
        'drop_percentage': 40.0,
        'ebay_price': 120.0,
        'potential_profit': 30.0,
        'profit_percentage': 50.0,
        'fallback_mode': False,
        'timestamp': '2024-01-01 00:00:00',
    }
    payload.update(overrides)
    return payload


def test_init_reads_channel_from_config(bot, config):
    assert bot.channel_id == config.DISCORD_CHANNEL_ID
    assert not bot.ready_event.is_set()


async def test_on_ready_sets_ready_event(bot):
    await bot.on_ready()

    assert bot.ready_event.is_set()
    await bot.wait_until_ready()


async def test_send_deal_notification_builds_embed(bot):
    channel = FakeChannel()
    use_channel(bot, channel)

    await bot.send_deal_notification(deal())

    assert len(channel.sent) == 1
    values = field_values(channel.sent[0])
    assert values['Product'] == 'Wireless Earbuds'
    assert values['Retailer'] == 'Target'
    assert values['Price Drop'] == '$100.00 → $60.00 (40.0%)'
    assert values['eBay Price'] == '$120.00'
    assert values['Potential Profit'] == '$30.00 (50.0%)'
    assert 'Note' not in values


async def test_send_deal_notification_in_fallback_mode(bot):
    channel = FakeChannel()
    use_channel(bot, channel)

    await bot.send_deal_notification(deal(fallback_mode=True))

    values = field_values(channel.sent[0])
    assert 'eBay Price' not in values
    assert values['Note'] == 'Price drop detected (eBay comparison unavailable)'


async def test_send_deal_notification_without_ebay_price(bot):
    channel = FakeChannel()
    use_channel(bot, channel)

    await bot.send_deal_notification(deal(ebay_price=None))

    assert 'eBay Price' not in field_values(channel.sent[0])


async def test_send_deal_notification_uses_defaults_for_missing_fields(bot):
    channel = FakeChannel()
    use_channel(bot, channel)

    await bot.send_deal_notification({})

    values = field_values(channel.sent[0])
    assert values['Product'] == 'Unknown'
    assert values['Price Drop'] == '$0.00 → $0.00 (0.0%)'
    assert values['Link'] == 'N/A'


async def test_send_deal_notification_without_channel_id(config):
    config.DISCORD_CHANNEL_ID = 0
    bot = DiscordBot(config)
    channel = FakeChannel()
    use_channel(bot, channel)

    await bot.send_deal_notification(deal())

    assert channel.sent == []


async def test_send_deal_notification_when_channel_missing(bot):
    bot.get_channel = lambda channel_id: None

    await bot.send_deal_notification(deal())


async def test_send_deal_notification_swallows_send_errors(bot):
    use_channel(bot, FakeChannel(error=RuntimeError('rate limited')))

    await bot.send_deal_notification(deal())


async def test_send_summary_limits_to_ten_deals(bot):
    channel = FakeChannel()
    use_channel(bot, channel)

    await bot.send_summary([deal(name=f'Deal {i}') for i in range(12)])

    embed = channel.sent[0]
    assert embed.title == '📊 Deal Summary - 12 New Deals'
    assert len(embed.fields) == 10
    assert embed.fields[0].name == '1. Deal 0'
    assert embed.fields[0].value == 'Drop: 40.0% | Profit: $30.00'


async def test_send_summary_ignores_empty_deal_list(bot):
    channel = FakeChannel()
    use_channel(bot, channel)

    await bot.send_summary([])

    assert channel.sent == []


async def test_send_summary_when_channel_missing(bot):
    bot.get_channel = lambda channel_id: None

    await bot.send_summary([deal()])


async def test_send_summary_swallows_send_errors(bot):
    use_channel(bot, FakeChannel(error=RuntimeError('rate limited')))

    await bot.send_summary([deal()])


async def test_send_error_notification(bot):
    channel = FakeChannel()
    use_channel(bot, channel)

    await bot.send_error_notification('scraper crashed')

    embed = channel.sent[0]
    assert embed.title == '⚠️ System Error'
    assert embed.description == 'scraper crashed'


async def test_send_error_notification_without_channel_id(config):
    config.DISCORD_CHANNEL_ID = None
    bot = DiscordBot(config)
    channel = FakeChannel()
    use_channel(bot, channel)

    await bot.send_error_notification('boom')

    assert channel.sent == []


async def test_send_error_notification_when_channel_missing(bot):
    bot.get_channel = lambda channel_id: None

    await bot.send_error_notification('boom')


async def test_send_error_notification_swallows_send_errors(bot):
    use_channel(bot, FakeChannel(error=RuntimeError('rate limited')))

    await bot.send_error_notification('boom')


async def test_start_bot_requires_token(config):
    config.DISCORD_BOT_TOKEN = None
    bot = DiscordBot(config)
    started = []
    bot.start = lambda token: started.append(token)

    await bot.start_bot()

    assert started == []


async def test_start_bot_starts_client_with_token(bot, config):
    started = []

    async def fake_start(token):
        started.append(token)

    bot.start = fake_start

    await bot.start_bot()

    assert started == [config.DISCORD_BOT_TOKEN]
