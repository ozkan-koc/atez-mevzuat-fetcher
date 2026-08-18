# ATEZ Resmî Gazete Fetcher

Basit ve ücretsiz GitHub Actions tabanlı Resmî Gazete fetcher'ı.

Şimdilik yalnız `resmigazete.gov.tr` hedeflenir. Mevzuat.gov.tr, Google Drive ve AI analiz katmanı bu sürümün kapsamı dışındadır.

## Akış

Hedef Türkiye tarihi (`YYYY-MM-DD`) için:

1. `https://www.resmigazete.gov.tr/DD.MM.YYYY` açılır.
2. Sayfadaki yalnız ana Resmî Gazete `/eskiler/YYYY/MM/YYYYMMDD-*` HTML/PDF linkleri çıkarılır.
3. İlan sayfaları ve başka tarihli linkler dışlanır.
4. Bulunan her HTML/PDF ham byte olarak indirilir.
5. Her request için ayrıntılı log ve manifest yazılır.
6. GitHub Actions run çıktısı 14 gün artifact olarak saklanır.

## 18 Ağustos 2026 doğrulaması

Gerçek GitHub-hosted Ubuntu runner üzerinde test edildi:

```text
Date:                 2026-08-18
Daily page:           HTTP 200
Documents discovered: 9
Documents fetched:    9
Status:               PASS
```

İndirilen resmi belgeler:

```text
20260818-1.htm
20260818-2.htm
20260818-3.htm
20260818-4.pdf
20260818-5.pdf
20260818-6.htm
20260818-7.htm
20260818-8.pdf
20260818-9.pdf
```

## TLS notu

GitHub runner'daki Python `requests`, `resmigazete.gov.tr` için standart sertifika doğrulamasında şu hatayı üretti:

```text
CERTIFICATE_VERIFY_FAILED
unable to get local issuer certificate
```

Fetcher önce TLS doğrulaması açık şekilde dener. Bu spesifik certificate-chain problemi görülür ve `verify=False` fallback başarılı olursa aynı run boyunca sonraki Resmî Gazete isteklerinde bu workaround yeniden kullanılır.

Bu durum manifestte gizlenmez:

```json
{
  "tls_verification": false,
  "fallback_reason": "known_certificate_chain_workaround"
}
```

Dolayısıyla bir dosyanın hangi URL'den ve hangi TLS yöntemiyle alındığı denetlenebilir.

## Çıktı

```text
python/out/YYYY-MM-DD/
  manifest.json
  raw/
    fihrist.html
    YYYYMMDD-1.htm
    YYYYMMDD-2.htm
    ...
    YYYYMMDD-9.pdf
```

`manifest.json` içinde her request için şunlar bulunur:

- source URL
- HTTP status
- final URL
- content type
- byte size
- elapsed time
- TLS verification durumu
- fallback nedeni
- success/failure

## Local kullanım

```bash
cd python
pip install requests beautifulsoup4 pytest
pytest -q
python rg_fetch.py 2026-08-18
```

## GitHub Actions

Workflow: `.github/workflows/python-rg.yml`

- Her gün `04:00 UTC` çalışır = `07:00 Europe/Istanbul`.
- Manuel çalıştırmada geçmiş bir `YYYY-MM-DD` tarihi verilebilir.
- Tarih boşsa `Europe/Istanbul` güncel tarihi kullanılır.
- Pull request sırasında yalnız unit testler çalışır; Resmî Gazete'ye network isteği gönderilmez.
- Gerçek scheduled/manual run çıktısı GitHub Actions artifact olarak 14 gün tutulur.

## Status

- `PASS`: günlük sayfa bulundu, en az bir ana Resmî Gazete belgesi keşfedildi ve keşfedilen belgelerin tamamı indirildi.
- `BLOCKED`: günlük sayfa alınamadı, ana belge seti çıkarılamadı veya belgelerden en az biri indirilemedi.
