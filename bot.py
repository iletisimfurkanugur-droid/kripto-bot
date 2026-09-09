import time
import requests

# ==========================================
# 1. BİLGİLER VE STRATEJİ AYARLARI
# ==========================================
API_KEY = "F042Cc12dC2E02d95434Cf93Afa8c12deSSZ1Vumsg2dxmst8gbKAJW3AR2ulyj4"
SECRET_KEY = "64C63A57A25Af55ac0a4771E824BAD31RmSmjVtSqOJixqgZX0RR7edUkm0hxNef"

SANAL_MOD = True  

# BAKİYE VE HEDEFLER
sanal_kasa_bakiyesi = 1000.0  # Başlangıç kasası
KAR_AL_ORANI = 20.0            # %20 Kâr hedefi
STOP_LOSS_ORANI = 3.0          # %3 Stop-Loss

# ENGELLENEN DEV ALTCOINLER VE SABİT COINLER (Hantal Coinler Elendi)
HARIC_COINLER = [
    'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'ADAUSDT', 'SOLUSDT', 
    'BNBUSDT', 'LTCUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT', 
    'TRXUSDT', 'USDCUSDT', 'TUSDUSDT', 'BUSDUSDT', 'EURUSDT', 
    'FDUSDUSDT', 'DAIUSDT'
]

aktif_pozisyon = None  # Aynı anda sadece 1 küçük altcoin/memecoin tutulacak
karantina_listesi = []

print("=" * 60)
print(f"🚀 KÜÇÜK ALTCOIN & MEMECOIN %20 PATLAMA BOTU BAŞLATILDI")
print(f"💰 Başlangıç Kasası: {sanal_kasa_bakiyesi:.2f} TL")
print(f"🎯 Hedef Kâr: %{KAR_AL_ORANI} | 🛑 Stop-Loss: %{STOP_LOSS_ORANI}")
print("🚫 Dev Altcoinler (BTC, ETH, XRP, SOL vb.) Tamamen Engellendi")
print("=" * 60 + "\n")

URL_LIST = [
    "https://api.binancetr.com/api/v3/ticker/24hr",
    "https://www.trbinance.com/open/v1/market/ticker/24hr",
    "https://api.binance.com/api/v3/ticker/24hr"
]

# ==========================================
# 2. ANA DÖNGÜ
# ==========================================
while True:
    try:
        data_list = []
        guncel_fiyatlar = {}

        for url in URL_LIST:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, dict) and 'data' in result:
                        data_list = result['data']
                    elif isinstance(result, list):
                        data_list = result
                    if data_list:
                        break
            except Exception:
                continue

        if not data_list:
            time.sleep(3)
            continue

        for item in data_list:
            symbol = item.get('symbol', '')
            fiyat = float(item.get('lastPrice', item.get('last', 0)))
            degisim = float(item.get('priceChangePercent', item.get('changeRate', 0)))
            if symbol and fiyat > 0:
                guncel_fiyatlar[symbol] = {'fiyat': fiyat, 'degisim': degisim}

        # --------------------------------------------------
        # A) AÇIK POZİSYON VARSA: TAKİP ET VE SAT
        # --------------------------------------------------
        if aktif_pozisyon:
            symbol = aktif_pozisyon['symbol']
            if symbol in guncel_fiyatlar:
                guncel_fiyat = guncel_fiyatlar[symbol]['fiyat']
                alis_fiyati = aktif_pozisyon['alis_fiyati']
                giris_bakiyesi = aktif_pozisyon['giris_bakiyesi']
                
                kar_zarar_yuzde = ((guncel_fiyat - alis_fiyati) / alis_fiyati) * 100
                net_tl_kazanc = (giris_bakiyesi * kar_zarar_yuzde) / 100
                clean_sym = symbol.replace('_', '')

                print(f"👀 [TAKİPTE] {clean_sym} | Alış: {alis_fiyati} -> Güncel: {guncel_fiyat} | Anlık Durum: %{kar_zarar_yuzde:+.2f}")

                # 🎯 KÂR AL SATIŞI (%20)
                if kar_zarar_yuzde >= KAR_AL_ORANI:
                    sanal_kasa_bakiyesi += net_tl_kazanc
                    print(f"\n🎯 [SANAL SATIŞ - %20 KÂR] {clean_sym}")
                    print(f"   Alış: {alis_fiyati} | Satış: {guncel_fiyat} | Kâr: %{kar_zarar_yuzde:.2f} (+{net_tl_kazanc:.2f} TL)")
                    print(f"   💰 YENİ TOPLAM KASA BAKİYESİ: {sanal_kasa_bakiyesi:.2f} TL\n")
                    aktif_pozisyon = None

                # 🛑 STOP-LOSS SATIŞI (%3)
                elif kar_zarar_yuzde <= -STOP_LOSS_ORANI:
                    sanal_kasa_bakiyesi += net_tl_kazanc
                    print(f"\n🛑 [SANAL SATIŞ - STOP LOSS] {clean_sym}")
                    print(f"   Alış: {alis_fiyati} | Satış: {guncel_fiyat} | Zarar: %{kar_zarar_yuzde:.2f} ({net_tl_kazanc:.2f} TL)")
                    print(f"   💰 YENİ TOPLAM KASA BAKİYESİ: {sanal_kasa_bakiyesi:.2f} TL\n")
                    aktif_pozisyon = None

        # --------------------------------------------------
        # B) AÇIK POZİSYON YOKSA: YENİ PATLAMAYA HAZIR ALTCOIN BUL
        # --------------------------------------------------
        else:
            for symbol, info in guncel_fiyatlar.items():
                clean_symbol = symbol.replace('_', '')
                
                # Sadece USDT çiftleri, Kara Listede olmayanlar ve Karantinada olmayanlar
                if not clean_symbol.endswith('USDT') or clean_symbol in HARIC_COINLER or symbol in karantina_listesi:
                    continue

                fiyat = info['fiyat']
                degisim_24h = info['degisim']

                # Erken Kırılım Eşiği (%2 ile %6 arası ivmelenmeye başlayanlar)
                if 2.0 <= degisim_24h <= 6.0:
                    print(f"\n🔥 [PATLAMA ADAYI YAKALANDI] {clean_symbol}")
                    print(f"   Fiyat: {fiyat} | 24s Değişim: %{degisim_24h:.2f}")
                    print(f"   🛒 Tüm Kasa ({sanal_kasa_bakiyesi:.2f} TL) ile sanal alım yapıldı. %20 Hedef Takipte!\n")
                    
                    aktif_pozisyon = {
                        'symbol': symbol,
                        'alis_fiyati': fiyat,
                        'giris_bakiyesi': sanal_kasa_bakiyesi
                    }
                    karantina_listesi.append(symbol)
                    break

        time.sleep(5)

    except Exception as e:
        print("Hata:", e)
        time.sleep(5)