import os
import math
import requests
import ccxt

# ============================================================
# DEBUG ENV (TEMPORAIRE)
# ============================================================

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT  = os.environ.get("TG_CHAT")

print("DEBUG TG_TOKEN exists :", TG_TOKEN is not None)
print("DEBUG TG_CHAT value  :", TG_CHAT)

# ============================================================
# CONFIG
# ============================================================

TIMEFRAMES = ["1h", "30m"]
BARS_LIMIT = 300

# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(text):
    if not TG_TOKEN or not TG_CHAT:
        print("[ERROR] Telegram not configured")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT, "text": text})

# ============================================================
# INDICATEURS TECHNIQUES
# ============================================================

def zlema(src, length):
    out = []
    ema = None
    alpha = 2/(length+1)
    lag = (length-1)//2
    for i,p in enumerate(src):
        adj = p if i < lag else 2*p - src[i-lag]
        ema = adj if ema is None else alpha*adj + (1-alpha)*ema
        out.append(ema)
    return out

def alma(src, length):
    m = (length-1)*0.9
    s = length/6
    w = [math.exp(-((i-m)**2)/(2*s*s)) for i in range(length)]
    w = [x/sum(w) for x in w]
    out = [None]*(length-1)
    for i in range(length-1,len(src)):
        out.append(sum(src[i-length+1+j]*w[j] for j in range(length)))
    return out

def ema(src,length):
    out=[]
    ema_val=None
    a=2/(length+1)
    for p in src:
        ema_val=p if ema_val is None else a*p+(1-a)*ema_val
        out.append(ema_val)
    return out

def rsi(src,length):
    gains=[0]; losses=[0]
    for i in range(1,len(src)):
        d=src[i]-src[i-1]
        gains.append(max(d,0))
        losses.append(max(-d,0))
    out=[None]*length
    ag=sum(gains[1:length+1])/length
    al=sum(losses[1:length+1])/length
    out.append(100-(100/(1+ag/al if al else 1)))
    for i in range(length+1,len(src)):
        ag=(ag*(length-1)+gains[i])/length
        al=(al*(length-1)+losses[i])/length
        out.append(100-(100/(1+ag/al if al else 1)))
    return out

def macdreact(close):
    if len(close) < 210:
        return False
    f = zlema(close,12)
    s = zlema(close,26)
    macd = [f[i]-s[i] for i in range(len(close))]
    sig = alma(macd,9)
    r   = rsi(close,5)
    ema200 = ema(close,200)
    i = -1
    return (
        macd[i] > sig[i] and macd[i-1] <= sig[i-1] and
        f[i] > f[i-1] and
        r[i] > r[i-1] and r[i] > 50 and
        close[i] > ema200[i]
    )

def heikin(ohlcv):
    ha=[]
    prev=(ohlcv[0][1]+ohlcv[0][4])/2
    for _,o,h,l,c,_ in ohlcv:
        hc=(o+h+l+c)/4
        ho=(prev+hc)/2
        ha.append(hc)
        prev=hc
    return ha

# ============================================================
# BINANCE SCAN (SAFE)
# ============================================================

binance = ccxt.binance()
binance.load_markets()

symbols = [
    s for s,m in binance.markets.items()
    if m.get("quote")=="USDC" and m.get("active", False)
][:50]

print("DEBUG symbols count :", len(symbols))

for sym in symbols:
    for tf in TIMEFRAMES:
        try:
            ohlcv = binance.fetch_ohlcv(sym, tf, limit=BARS_LIMIT)
            ha = heikin(ohlcv)
            if macdreact(ha):
                msg = f"FINAL ENTRY\n{sym}\nTF {tf}\nMACDreact + EMA200"
                print(msg)
                send_telegram(msg)
        except Exception as e:
            print(f"[SKIP] {sym} {tf} → {e}")

print("[DONE] Script finished")
