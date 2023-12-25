import time
import aiohttp
import io
import matplotlib.pyplot as plt
from tabulate import tabulate
import hashlib
import random
import requests
import discord
from discord.ext import commands, tasks
from pd import pd
import re
from datetime import datetime, timedelta
import pytz 
from itertools import zip_longest, chain
import asyncio
from  echoesmobi_wrap import getdic
import traceback



async def setup(bot):
    l = killdigest_cog(bot)
    await bot.add_cog(l)
    l.keeper.start()
    try:
        await l.kdcfg(None)
    except:
        traceback.print_exc()

trashbin = '\U0001F5D1'
guid = 871762312208474133
uid4o = 139179662369751041
cid = 1092302014647640125
mf = '%Y-%m-%d %H:%M:%S:%f'
jonid = 339395756568084482
jonid = 466724591109144588

def tostr(d):
    return d.strftime(mf)

def fromstr(s):
    return datetime.strptime(s, mf)

def iskf(total):
    for i in [(1e9, 'b'), (1e6, 'm'), (1e3, 'k')]:
        if total > i[0]:
            t = '{:.2f}'.format(total/i[0])
            total = f'{t}{i[1]}'
            break
    return total

def parse_cfg(s):
    a = s.split('\n')[1:-1]
    return {x.split()[0]: x.split()[1:] for x in a}

class killdigest_cog(commands.Cog):
    def __init__(self, bot):
        print('ppk module loaded')
        self.bot = bot
        self.pd = pd('killdigest.json')
        if 'week' not in self.pd:
            self.pd['week'] = 0
            self.pd.sync()
        self.scanning = False

    @commands.command()
    async def kdcfg(self, ctx):
        if 'cfg' not in self.pd:
            c = discord.utils.get(self.bot.get_guild(746879468940820560).channels, id = 1173599457531662366) 
            self.pd['cfg'] = (await c.send('cfg:\n\nreply to this message to change config')).id
            self.pd.sync()
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id != 1173599457531662366:
            return
        rid = message.reference.message_id
        if rid == self.pd['cfg']:
            msg = await message.channel.fetch_message(rid)
            txt = f'cfg:\n{message.content}\nreply to this message to change config'
            await msg.edit(content = txt)

    @commands.command()
    async def killscanner(self, ctx, daysn = 4):
        if self.scanning:
            await ctx.send('please wait for previous request to complete')
            return
        f = '%m-%d-%Y'
        e = datetime.now(pytz.utc)
        s = (e - timedelta(days = daysn)).strftime(f)
        e = e.strftime(f)
        url = f'https://echoes.mobi/killboard/export/{s}/{e}/json'
        #txt = requests.get(url).json()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                m = await ctx.send('poking echoes.mobi')
                self.scanning = True
                try:
                    txt = await resp.json()
                except:
                    self.scanning = False
                    await m.edit(content = m.content + f'...crashed. url {url}')
                    return
                self.scanning = False
                await m.edit(content = m.content + '...done')
        if ctx.author.id == 139179662369751041:
            with open('echoesdump.json', 'w') as f:
                json.dump(txt, f)
        d = {}
        for i in txt:
            s = i["system"]
            c = i["constellation"]
            r = i["region"]
            if r not in d:
                d[r] = {'n': 0, 'kms': {}}
            if c not in d[r]['kms']:
                d[r]['kms'][c] = {'n': 0, 'kms': {}}
            if s not in d[r]['kms'][c]['kms']:
                d[r]['kms'][c]['kms'][s] = []
            d[r]['kms'][c]['kms'][s].append(i)
            d[r]['n'] += 1
            d[r]['kms'][c]['n'] += 1
        txt = ''
        for k, v in sorted(d.items(), reverse = True, key = lambda x: x[1]['n']):
            txt += f'{k}: {v["n"]}\n'
#            for k, v in sorted(v['kms'].items(), reverse = True, key = lambda x: x[1]['n']):
#                txt += f'    {k}: {v["n"]}\n'
#                for k, v in sorted(v['kms'].items(), reverse = True, key = lambda x: len(x[1])):
#                    txt += f'        {k}: {len(v)}\n'
        tmp = ''
        for i in txt.split('\n'):
            if len(i)+ len(tmp) > 1900:
                await ctx.send(tmp)
                tmp = i
            else:
                tmp += '\n' + i
        await ctx.send(tmp)

    @commands.command()
    async def testit(self, ctx):
        await ppk_do(self, self.bot, ctx)

    async def getcorpdic(self, ctx):
        f = '%m-%d-%Y'
        today = datetime.now(pytz.utc)
        start_date = today - timedelta(days=today.weekday() + 7)
        e = (start_date + timedelta(days=7)).strftime(f)
        s = start_date.strftime(f)
        url = f'https://echoes.mobi/killboard/export/{s}/{e}/json'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                m = await ctx.send('poking echoes.mobi')
                try:
                    l = await resp.json()
                except:
                    await m.edit(content = m.content + f'...crashed. url {url}')
                    return
                self.scanning = False
                await m.edit(content = m.content + '...done')
        c = discord.utils.get(self.bot.get_guild(746879468940820560).channels, id = 1173599457531662366) 
        cfg_msg = await c.fetch_message(self.pd['cfg'])
        cfg = parse_cfg(cfg_msg.content)
        kills = {x: {k: [] for k in cfg.keys()} for x in ['provi', 'ext']}
        losses = {x: {k: [] for k in cfg.keys()} for x in ['provi', 'ext']}
        shipcats = []
        capkills = []
        caplosses = []
        capclasses = ['Versatile Assault Ship', 'Carrier', 'Industrial Command Ship', 'Dreadnought', 'Supercarrier', 'Force Auxiliary', 'Capital Industrial Ship']
        for i in l:
            for n in ['killer_ship_category', 'victim_ship_category']:
                sc = i[n]
                if sc not in shipcats:
                    shipcats.append(sc)
            for corp in cfg:
                if i['region'] == 'Providence':
                    kmk = 'provi'
                else:
                    kmk = 'ext'
                if i['killer_corp'] == corp:
                    kills[kmk][corp].append(i)
                    if i['victim_ship_category'] in capclasses:
                        if i['isk'] > 10000000000:
                            capkills.append(i['image_url'])
                if i['victim_corp'] == corp:
                    losses[kmk][corp].append(i)
                    if i['victim_ship_category'] in capclasses:
                        if i['isk'] > 10000000000:
                            caplosses.append(i['image_url'])
        txt = ''
        headers = {'provi': 'domestic', 'ext': 'foreign'}
        msgs = []
        zeroar = []
        for kmk in ['provi', 'ext']:
            def kill_isk(n):
                return sum([float(x['isk']) for x in kills[kmk][n]])
            def loss_isk(n):
                return sum([float(x['isk']) for x in losses[kmk][n]])
            cfg = sorted(cfg, reverse = True, key = lambda x: (kill_isk(x), -loss_isk(x)))
            txt = headers[kmk] + ' pvp:\n'
            zeros = []
            header = ['corp', 'kills', 'losses']
            l = []
            for i in cfg:
                kmn = len(kills[kmk][i])
                kisk = kill_isk(i)
                lsn = len(losses[kmk][i])
                lisk = loss_isk(i)
                if kmn == 0 and lsn == 0:
                    zeros.append(i)
                    continue
                if kmn:
                    kms = f'{iskf(kisk)} in {kmn} kms'
                else:
                    kms = 'no kills'
                if lsn:
                    lss = f'{iskf(lisk)} in {lsn}kms'
                else:
                    lss = 'no losses woohoo'
                l.append([i, kms, lss])
            txt += '```\n' + tabulate(l, header, tablefmt = 'github') + '```\n'
            zeroar.append(zeros)
            msgs.append(txt)
        msgs.append(f'no pvp action at all in: {set(zeroar[0]).intersection(set(zeroar[1]))}')
        l = []
        if capkills:
            l.append('cap kills:')
            l.extend(capkills)
        else:
            l.append('no cap kills')
        if caplosses:
            l.append('cap losses:')
            l.extend(caplosses)
        else:
            l.append('no cap losses')
        msgs.append('\n'.join(l))
        return msgs

    @commands.command()
    async def provi(self, ctx):
        try:
            a, b, _ = await get({'order[date_killed]': 'desc','region': 'providence'})
            await ctx.send(a)
            await ctx.send(b)
        except Exception as e:
            await ctx.send(traceback.format_exc())


    @commands.command()
    async def hellkms(self, ctx):
        try:
            d = await get({'order[date_killed]': 'desc','constellation': 'NJU-QV'}) + '\n'
            d += await get({'order[date_killed]': 'desc','constellation': 'Basilisk'})
            await ctx.send(d)
        except Exception as e:
            await ctx.send(str(e))

    @commands.command()
    async def plotkmregions(self, ctx, limit: int = 1):
        cfg = {'order[date_killed]': 'desc', 'region': 'Providence'}
        o = getdic(cfg)
        today = datetime.now(pytz.utc)
        start_date = today - timedelta(days=today.weekday())
        ret = {}
        for i in o:
            n = int((start_date - i['date_killed']).days/7)
            if n > limit:
                break
            n = i['constellation']
            if n not in ret:
                ret[n] = 0
            ret[n] += float(i['isk'])/1000000
        f = generate_column_graph(ret)
        s = '\n'.join([f'{k}: {v}' for k, v in ret.items()])
        await ctx.send('theres a bug with labels so weeks on x, mil isk on y\n' + s, file = f)

    @commands.command()
    async def plotkm(self, ctx, *name, limit: int = 12):
        name = ' '.join(name)
        cfg = {'order[date_killed]': 'desc', 'killer_name': name}
        o = getdic(cfg)
        today = datetime.now(pytz.utc)
        start_date = today - timedelta(days=today.weekday())
        ret = {}
        for i in o:
            n = int((start_date - i['date_killed']).days/7)
            if n > limit:
                break
            if n not in ret:
                ret[n] = 0
            ret[n] += float(i['isk'])/1000000
        f = generate_column_graph(ret)
        s = '\n'.join([f'{k}: {v}' for k, v in ret.items()])
        await ctx.send('theres a bug with labels so weeks on x, mil isk on y\n' + s, file = f)

    @commands.command()
    async def crubrus(self, ctx, cmd = None, limit: int = 12):
        arg = cmd
        try:
            if arg == 'plot':
                cfg = {'order[date_killed]': 'desc', 'killer_name': 'Crubrus', 'killer_ship_type' : 'Daredevil'}
                o = getdic(cfg)
                today = datetime.now(pytz.utc)
                start_date = today - timedelta(days=today.weekday())
                ret = {}
                for i in o:
                    n = int((start_date - i['date_killed']).days/7)
                    if n > limit:
                        break
                    if n not in ret:
                        ret[n] = 0
                    ret[n] += float(i['isk'])/1000000
                f = generate_column_graph(ret)
                await ctx.send('no limit to what that dd can kill:\n', file = f)
            else:
                arg = int(arg)
                if arg > 0:
                    arg = -arg
                cfg = {'order[date_killed]': 'desc', 'killer_name': 'Crubrus', 'killer_ship_type' : 'Daredevil'}
                o = getdic(cfg)
                wn = -arg
                today = datetime.now(pytz.utc)
                if arg == 0:
                    start_date = today - timedelta(days=today.weekday())
                    end_date = today
                else:
                    start_date = today - timedelta(days=today.weekday() + 7*wn)
                    end_date = start_date + timedelta(days=7*wn)
                ret = {}
                for i in o:
                    if i['date_killed'] < start_date:
                        break
                    elif i['date_killed'] > end_date:
                        pass
                    else:
                        st = i['victim_ship_type']
                        if st not in ret:
                            ret[st] = 0
                        ret[st] += 1
                m = 'no limit to what that dd can kill:\n'
                tail = []
                dd = {}
                for k, v in sorted(ret.items(), reverse = True, key = lambda x: x[1]):
                    if str(v) not in dd:
                        dd[str(v)] = []
                    dd[str(v)].append(k)
                for k, v in dd.items():
                    m += f'{k}: {", ".join(v)}\n'
                    if len(m) > 1800:
                        await ctx.send(m)
                        m = ''
                if m:
                    await ctx.send(m)
                await ctx.send(f'others: {", ".join(tail)}')
        except Exception as e:
            await ctx.send(str(e))

    @tasks.loop(hours = 8)
    async def keeper(self, force = False):
        await ppk_do(self, self.bot)

async def ppk_do(self, b, channel = None):
    force = True
    if not channel:
        force = False
        channel_id = 1172107713031979008
        channel = b.get_channel(channel_id)
    today = datetime.utcnow()
    start_date = today - timedelta(days=today.weekday() + 7)
    end_date = start_date + timedelta(days=7)
    week = (start_date + timedelta(1)).isocalendar()[1]
    if (self.pd['week'] != week) or force:
        a, b, _ = await get({'order[date_killed]': 'desc','region': 'providence'})
        txt = await self.getcorpdic(channel)
        for i in [a, b, *txt]:
            try:
                await channel.send(str(i))
            except:
                await channel.send('failed to send this msg')

        self.pd['week'] = week
        self.pd.sync()

async def get(c = {'order[date_killed]': 'desc','region': 'providence'}):
    if isinstance(c, list):
        o = chain([getdic(x) for x in c])
    else:
        o = getdic(c)
    today = datetime.now(pytz.utc)
    start_date = today - timedelta(days=today.weekday() + 7)
    end_date = start_date + timedelta(days=7)
    last = None
    n = 0
    corps = {}
    isk = {}
    iskt = 0
    kms = []
    async for i in o:
        if i['date_killed'] < start_date:
            new = 'less'
        elif i['date_killed'] > end_date:
            new = 'more'
        else:
            kms.append(i)
            new = 'ok'
            n += 1
            kc = i['killer_corp']
            if kc not in corps:
                corps[kc] = 0
            corps[kc] += 1
            if kc not in isk:
                isk[kc] = 0
            iskt += float(i['isk'])
            isk[kc] += float(i['isk'])
        if new != last:
            print(new)
            last = new
        if last == 'less':
            break
    s = f'weekly kill digest for providence:\ntotal:{int(iskt/1000000000)} bil in {n} kills\n'
    for k, v in sorted(isk.items(), reverse = True, key = lambda x:x[1]):
        s += f'{k}: {corps[k]} / {int(100*corps[k]/n)}% ({int(isk[k]/1000000000)} bil isk / {int(100*isk[k]/iskt)}%)\n'
    if len(s) > 1900:
        s = s[:1900]
    l = []
    header = ['system', 'killer_full_name', 'victim_full_name', 'victim_ship_type', 'isk', '%']
    for i in list(sorted(kms, reverse = True, key = lambda x: float(x['isk'])))[:10]:
        l.append([i["system"], i["killer_full_name"], i["victim_full_name"], i["victim_ship_type"], i["isk"], int(100*float(i["isk"])/iskt)])
    s2 = '````\n' + tabulate(l, header, tablefmt = 'github') + '```'
    return s, s2, kms

def generate_column_graph(d):
    # Example data
    labels = list(d.keys())
    values = list(d.values())

    # Create the graph
    p = plt.figure(figsize = (len(labels), len(values)))
    plt.bar(labels, values)
    plt.xlabel = 'weeks'
    plt.ylabel = 'mil isk isk'
    plt.tight_layout()

    # Save the graph to a buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='jpg')
    buffer.seek(0)

    # Create a discord.File object from the buffer
    graph_file = discord.File(buffer, filename='graph.jpg')

    return graph_file


