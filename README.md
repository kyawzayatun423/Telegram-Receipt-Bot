# MLBB Order Receipt Bot — Setup Guide

## လုပ်ဆောင်ချက် အကျဉ်းချုပ်

1. Customer က Group ထဲမှာ ပြေစာပုံ + `UID Order` စာသား (ဥပမာ `1354119674 15566 86 Diamonds`) ပို့သည်။
2. Bot က message ကို read လုပ်ပြီး **UID** နဲ့ **Order** ကို ခွဲထုတ်သိမ်းထားသည် (နောက်ဆုံး token ၂ ခုက Order၊ ကျန်တာက UID)။
3. **Admin (Telegram ID: `7978208335`) သာလျှင်** customer ရဲ့ order message ကို **Reply** လုပ်ပြီး Order စာသားကို command နောက်မှာ တိုက်ရိုက်ထည့်ရိုက်နိုင်သည်:
   - `/.86 Diamonds`  → Approve, Order = "86 Diamonds"
   - `/-86 Diamonds`  → Reject,  Order = "86 Diamonds"
   (command နဲ့ order စာကြားမှာ space ခံပြီး `/. 86 Diamonds` လို့ရေးလည်း ရပါတယ်)
   Order text မထည့်ဘဲ bare `/.` သို့မဟုတ် `/-` ပဲ ရိုက်ရင် Bot က customer ရဲ့ message ထဲက auto-parse ဖြစ်ခဲ့တဲ့ order (ရှိခဲ့ရင်) ကို fallback အနေနဲ့ သုံးပါလိမ့်မယ်။
   Admin မဟုတ်သူတွေ ဒီ command ရိုက်လည်း Bot က လျစ်လျူရှုသည်။
4. Bot က customer ရဲ့ message ကို reply လုပ်ပြီး `#Order Receipt -MLBB` ပုံစံနဲ့ ရလဒ် (admin ရိုက်ထည့်တဲ့ Order၊ Serial၊ Yangon time စသည်) ကို Group ထဲမှာ ထုတ်ပေးသည်။

## Setup လုပ်ရမည့် အဆင့်များ

### 1. Bot Token ယူပါ
- Telegram ထဲမှာ **@BotFather** ကို ရှာပြီး `/newbot` command သုံးပါ။
- Bot name/username ပေးပြီး **API Token** ကို copy ယူထားပါ။

### 2. Bot ကို Group ထဲ ထည့်ပါ
- Bot ကို target Group ထဲ Add လုပ်ပါ။
- Group Privacy Mode ကို ပိတ်ဖို့လိုပါမယ် — @BotFather မှာ `/mybots` → Bot ရွေး → **Bot Settings** → **Group Privacy** → **Turn off**
  (ဒါမှ Bot က group ထဲက message အားလုံးကို ဖတ်နိုင်မှာပါ — customer order caption/text ဖတ်ဖို့ လိုအပ်ပါတယ်)

### 3. Group Chat ID ရှာပါ
Group Chat ID ကို ရှာနည်း (တစ်ခုခုရွေးပါ):
- Bot ကို group ထဲ add ပြီးမှ, group ထဲမှာ တစ်စုံတစ်ခု ရိုက်ပြီး ဒီ URL ကို browser မှာဖွင့်ပါ:
  `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
  → `"chat":{"id": -1001234567890, ...}` ဆိုတဲ့ negative number ကို ယူပါ (group/supergroup id တွေက အနုတ်ဂဏန်းဖြစ်ပါတယ်)။

### 4. Environment Variables သတ်မှတ်ပါ
```bash
export BOT_TOKEN="123456:ABC-your-real-bot-token"
export GROUP_CHAT_ID="-1001234567890"
export ADMIN_ID="7978208335"   # optional — code default ဘဲ ၇၉၇၈၂၀၈၃၃၅ ဖြစ်နေပါပြီ
```

### 5. Dependencies Install
```bash
pip install -r requirements.txt
```

### 6. Bot ကို Run
```bash
python3 bot.py
```

Bot က polling mode နဲ့ run နေမှာဖြစ်ပြီး, terminal ကို ပိတ်ရင် bot ရပ်သွားမှာမို့ VPS/server တစ်ခုပေါ်မှာ
`screen`, `tmux`, သို့မဟုတ် `systemd` service အနေနဲ့ background မှာ ထားအလုပ်လုပ်ပါစေဖို့ recommend ပါတယ်။

## UID / Order Rule

**UID (customer message ကနေ auto ယူသည်):**
`1354119674 15566 86 Diamonds` ဆိုတဲ့ customer text ကို space-separated tokens အဖြစ်ခွဲပြီး **နောက်ဆုံး ၂ token ကို ချန်ထားလိုက်တဲ့ ကျန်တဲ့ tokens အားလုံး** ကို **UID** အဖြစ်ယူသည် (ဒီနေရာမှာ `1354119674 15566`)။ Photo caption ထဲမှာဖြစ်ဖြစ်, plain text message ထဲမှာဖြစ်ဖြစ် ဒီပုံစံနဲ့ ရေးထားရင် Bot က UID ကို မှတ်သားပါလိမ့်မယ်။

**Order (admin ရိုက်ထည့်ရမည်):**
Auto-parse မလုပ်တော့ဘဲ Admin က Approve/Reject command **နောက်မှာ Order စာကို တိုက်ရိုက်ရိုက်ထည့်ရပါမယ်**:
```
/.86 Diamonds     ->  Situation: Approve,  Order: 86 Diamonds
/-86 Diamonds     ->  Situation: Reject,   Order: 86 Diamonds
```
Order text မပါဘဲ bare `/.` / `/-` ပဲ ရိုက်ရင် Bot က customer message ထဲက auto-detect ဖြစ်ခဲ့တဲ့ order (ရှိခဲ့ရင်) ကို fallback အနေနဲ့ သုံးပြီး၊ လုံးဝမရှိရင် admin ကို "Order text ထည့်ပါ" ဆိုပြီး Bot က warning ပြန်ပေးပါလိမ့်မယ်။

## GitHub + Render နဲ့ 24/7 Run နည်း (Local server မလိုအပ်ဘဲ Cloud ပေါ်မှာ အမြဲဖွင့်ထားနိုင်ဖို့)

Terminal ကို ပိတ်ရင် bot ရပ်နေတာမကြိုက်ရင် **Render.com** (Background Worker, free tier ရှိသည်) ပေါ်မှာ GitHub repo ကနေ တိုက်ရိုက် run နိုင်ပါတယ်။ `render.yaml` ကို ဒီ repo ထဲမှာ ထည့်ပေးထားပြီးသားပါ။

1. **GitHub repo ဆောက်ပါ** — `bot.py`, `requirements.txt`, `render.yaml`, `.gitignore` (README လည်း) ကို repo အသစ်ထဲ push လုပ်ပါ။
2. **render.com** မှာ account ဖွင့်ပြီး **New +** → **Blueprint** ရွေးပါ (render.yaml ကို auto-detect လုပ်ပါလိမ့်မယ်)၊ GitHub repo ကို connect လုပ်ပါ.
   - Blueprint မသုံးချင်ရင် **New +** → **Background Worker** ကို manual ရွေးလည်းရပါတယ် — Build Command: `pip install -r requirements.txt`, Start Command: `python3 bot.py`.
3. **Environment Variables** ထည့်ပါ (Render dashboard → Environment):
   - `BOT_TOKEN` = BotFather ကပေးတဲ့ token
   - `GROUP_CHAT_ID` = သင့် Group ရဲ့ negative chat id
   - `ADMIN_ID` = `7978208335` (render.yaml ထဲမှာ default ထည့်ပြီးသား)
4. **Deploy** ကိုနှိပ်ပါ — Render က repo ကို build လုပ်ပြီး Background Worker အဖြစ် run ပါလိမ့်မယ်။ Web Service မဟုတ်ဘဲ Worker ဖြစ်လို့ port bind စရာမလိုပါ (polling bot မို့ပါ)။
5. **Logs စစ်ပါ** — Render dashboard → Logs tab မှာ `Bot starting… admin_id=7978208335 group_chat_id=...` ဆိုတဲ့ line ပေါ်ရင် bot အလုပ်လုပ်နေပြီ။
6. **Auto-redeploy** — GitHub repo ကို code အသစ် push လုပ်တိုင်း Render က auto-detect လုပ်ပြီး ပြန် deploy လုပ်ပေးပါလိမ့်မယ် (Blueprint/Auto-Deploy on ထားရင်).

> Note: Render free tier Background Worker တွေက web service လိုမျိုး "sleep" မဖြစ်ပါဘူး (Web Service free tier ကသာ inactivity ကြောင့် sleep ဖြစ်တတ်တာ) — ဒါပေမဲ့ Render ရဲ့ free-tier limits/policy တွေက အချိန်နဲ့အမျှ ပြောင်းလဲနိုင်လို့ dashboard ထဲက “Free” plan details ကို အမြဲ double-check လုပ်ပါ။ Production/reliable ဖို့ဆိုရင် paid plan (သို့) VPS + `systemd`/`tmux` ကို recommend ပါတယ်။



- Orders တွေက **memory ထဲမှာပဲ** သိမ်းထားတာမို့ Bot ပြန် restart လုပ်ရင် approve/reject မလုပ်ရသေးတဲ့ order များ ပျောက်သွားနိုင်ပါတယ်။ Production အတွက် production-grade လိုချင်ရင် SQLite/JSON file ထည့်ပေးနိုင်ပါတယ်, ပြောနိုင်ပါတယ်။
- Admin ID တစ်ယောက်ထဲပဲ (`7978208335`) approve/reject လုပ်ခွင့်ရှိပါတယ်။ Admin ထပ်ထည့်ချင်ရင် `ADMIN_ID` ကို list of IDs အဖြစ် ပြောင်းပေးနိုင်ပါတယ်။
- Group ID သတ်မှတ်မထားရင် (`GROUP_CHAT_ID=0`) Bot ထည့်ထားတဲ့ Chat/Group *တိုင်း*မှာ အလုပ်လုပ်ပါလိမ့်မယ် — Group တစ်ခုတည်း ကန့်သတ်ချင်ရင် `GROUP_CHAT_ID` ကို အမှန်ထည့်ပါ။
