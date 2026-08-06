from telethon import events, types
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import os

# Telegram ID lari va ularga mos keluvchi ro'yxatdan o'tish vaqtlari (Interpolatsiya uchun)
REG_DATA = {
    "1000000": 1380326400, "2768409": 1383264000, "7679610": 1388448000, "11538514": 1391212000,
    "15835244": 1392940000, "23646077": 1393459000, "38015510": 1393632000, "44634663": 1399334000,
    "46145305": 1400198000, "54845238": 1411257000, "63263518": 1414454000, "101260938": 1425600000,
    "101323197": 1426204000, "103151531": 1433376000, "103258382": 1432771000, "109393468": 1439078000,
    "111220210": 1429574000, "112594714": 1439683000, "116812045": 1437696000, "122600695": 1437782000,
    "124872445": 1439856000, "125828524": 1444003000, "130029930": 1441324000, "133909606": 1444176000,
    "143445125": 1448928000, "148670295": 1452211000, "152079341": 1453420000, "157242073": 1446768000,
    "171295414": 1457481000, "181783990": 1460246000, "222021233": 1465344000, "225034354": 1466208000,
    "278941742": 1473465000, "285253072": 1476835000, "294851037": 1479600000, "297621225": 1481846000,
    "328594461": 1482969000, "337808429": 1487707000, "341546272": 1487782000, "352940995": 1487894000,
    "369669043": 1490918000, "400169472": 1501459000, "616816630": 1529625600, "681896077": 1532821500,
    "727572658": 1543708800, "796147074": 1541371800, "925078064": 1563290000, "928636984": 1581513420,
    "1054883348": 1585674420, "1057704545": 1580393640, "1145856008": 1586342040, "1227964864": 1596127860,
    "1382531194": 1600188120, "1658586909": 1613148540, "1660971491": 1613329440, "1692464211": 1615402500,
    "1719536397": 1619293500, "1721844091": 1620224820, "1772991138": 1617540360, "1807942741": 1625520300,
    "1893429550": 1622040000, "1972424006": 1631669400, "1974255900": 1634000000, "2030606431": 1631992680,
    "2041327411": 1631989620, "2078711279": 1634321820, "2104178931": 1638353220, "2120496865": 1636714020,
    "2123596685": 1636503180, "2138472342": 1637590800, "3318845111": 1618028800, "4317845111": 1620028800,
    "5162494923": 1652449800, "5186883095": 1648764360, "5304951856": 1656718440, "5317829834": 1653152820,
    "5318092331": 1652024220, "5336336790": 1646368100, "5362593868": 1652024520, "5387234031": 1662137700,
    "5396587273": 1648014800, "5409444610": 1659025020, "5416026704": 1660925460, "5465223076": 1661710860,
    "5480654757": 1660926300, "5499934702": 1662130740, "5513192189": 1659626400, "5522237606": 1654167240,
    "5537251684": 1664269800, "5559167331": 1656718560, "5568348673": 1654642200, "5591759222": 1659025500,
    "5608562550": 1664012820, "5614111200": 1661780160, "5666819340": 1664112240, "5684254605": 1662134040,
    "5684689868": 1661304720, "5707112959": 1663803300, "5756095415": 1660925940, "5772670706": 1661539140,
    "5778063231": 1667477640, "5802242180": 1671821040, "5853442730": 1674866100, "5859878513": 1673117760,
    "5885964106": 1671081840, "5982648124": 1686941700, "6020888206": 1675534800, "6032606998": 1686998640,
    "6057123350": 1676198350, "6058560984": 1686907980, "6101607245": 1686830760, "6108011341": 1681032060,
    "6132325730": 1692033840, "6182056052": 1687870740, "6279839148": 1688399160, "6306077724": 1692442920,
    "6321562426": 1688486760, "6364973680": 1696349340, "6386727079": 1691696880, "6429580803": 1692082680,
    "6527226055": 1690289160, "6813121418": 1698489600, "6865576492": 1699052400, "6925870357": 1701192327,
    "7000000000": 1711889200, "7100000000": 1719772800, "7200000000": 1725148800, "7350000000": 1730454400,
    "7500000000": 1735776000, "7700000000": 1740960000, "7850000000": 1743638400, "8000000000": 1746316800,
    "8200000000": 1748995200, "8350000000": 1751673600, "8500000000": 1754352000,
}

class RegistrationEstimator:
    def __init__(self, order: int = 3):
        x_data = np.array(list(map(int, REG_DATA.keys())))
        y_data = np.array(list(REG_DATA.values()))
        fitted = np.polyfit(x_data, y_data, order)
        self._func = np.poly1d(fitted)

    def estimate(self, tg_id: int):
        value = self._func(tg_id)
        return min(value, time.time())

estimator = RegistrationEstimator()

def calculate_age(date_str):
    reg_date = datetime.strptime(date_str, "%d.%m.%Y")
    current_date = datetime.now()
    diff = relativedelta(current_date, reg_date)
    
    parts = []
    if diff.years > 0: parts.append(f"{diff.years} yil")
    if diff.months > 0: parts.append(f"{diff.months} oy")
    if diff.days > 0: parts.append(f"{diff.days} kun")
    
    return ", ".join(parts) if parts else "Yangi akkunt"

async def setup_account_info(client):
    @client.on(events.NewMessage(pattern=r'\.acc(?: (.*))?', outgoing=True))
    async def acc_handler(event):
        """Akkunt haqida ma'lumot olish"""
        args = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        
        await event.edit("✅ <b>Ma'lumotlar qidirilmoqda...</b>", parse_mode='html')
        
        try:
            if reply:
                user = await client.get_entity(reply.sender_id)
            elif args:
                try:
                    if args.isdigit():
                        user = await client.get_entity(int(args))
                    else:
                        user = await client.get_entity(args)
                except Exception:
                    await event.edit("🚫 <b>Foydalanuvchi topilmadi!</b>", parse_mode='html')
                    return
            else:
                user = await client.get_me()

            user_id = user.id
            dc_id = user.photo.dc_id if user.photo else "Noma'lum"
            
            reg_time = round(estimator.estimate(user_id))
            reg_date = datetime.utcfromtimestamp(reg_time).strftime("%d.%m.%Y")
            age_str = calculate_age(reg_date)
            
            info_text = (
                f"✅ <b>{user.first_name} haqida ma'lumot</b>:\n\n"
                f"💎 <b>ID:</b> <code>{user_id}</code>\n"
                f"✈️ <b>Data-center:</b> <code>{dc_id}</code>\n"
                f"✅ <b>Ochilgan sana:</b> <code>{reg_date}</code>\n"
                f"🎲 <b>Akkunt yoshi:</b> <code>{age_str}</code>"
            )
            
            await event.edit(info_text, parse_mode='html')
            
        except Exception as e:
            await event.edit(f"🚫 <b>Xatolik:</b> <code>{e}</code>", parse_mode='html')
