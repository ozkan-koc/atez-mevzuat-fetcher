# ATEZ Mevzuat Collector

GitHub Actions üzerinde çalışan, Resmî Gazete kanıtlarını ve iki yardımcı keşif kaynağını günlük artifact olarak üreten kolektör.

Bu depo yalnız veri toplar. Mevzuat analizi, rapor üretimi, Google Drive arşivleme ve e-posta teslimi scheduled task içindeki ayrı skill'lerin sorumluluğudur.

## Kaynak politikası

- **Resmî kanıt:** `resmigazete.gov.tr`
- **Yardımcı, bağlayıcı olmayan kaynaklar:** Tariff ve Resmî Gazete Özeti
- Yardımcı kaynaklar hiçbir zaman hukuki kanıt yerine kullanılamaz.
- Resmî bir indirme farklı hosta yönlenirse veya dosya imzası uzantıyla uyuşmazsa dosya reddedilir ve run `BLOCKED` olur.

## Çalışma akışı

1. Hedef tarih `YYYY-MM-DD` olarak doğrulanır.
2. Günlük Resmî Gazete fihristi bulunur.
3. Yalnız aynı tarihe ait, izinli hosttaki ana HTML/PDF belgeleri keşfedilir.
4. İndirilen içerik host, content type ve HTML/PDF imzasıyla doğrulanır.
5. Yardımcı kaynaklar ayrı sınıfta toplanır.
6. Tarih klasörü atomik olarak yayımlanır; önceki denemeden stale dosya kalmaz.
7. `manifest.json`, run durumu ve SHA-256 dosya envanterini içerir.

## Çıktı sözleşmesi

```text
python/out/YYYY-MM-DD/
├── manifest.json
├── supporting-sources.json
└── raw/
    ├── official/
    │   ├── fihrist.html
    │   └── YYYYMMDD-N.{htm,pdf}
    └── supporting/
        ├── tariff-latest.json
        └── resmi-gazete-ozeti.html
```

`manifest.json` için temel alanlar:

- `schema_version: "1.0"`
- `artifact_version: "atez-collector/v1"`
- `status: PASS | BLOCKED`
- keşfedilen/indirilen belgeler ve request kayıtları
- resmi/yardımcı kaynak ayrımı
- her non-manifest dosya için `path`, `role`, `media_type`, `bytes`, `sha256`

`PASS`, en az bir resmî belge keşfedildiği ve tamamının doğrulanarak indirildiği anlamına gelir. Yardımcı kaynak hataları kaydedilir ancak resmî kanıt seti tam ise sonucu bozmaz. `BLOCKED` çıktısı da tanı için artifact olarak yüklenir.

## Yerel kullanım

```bash
cd python
python -m pip install -e ".[test]"
pytest
python rg_fetch.py 2026-08-18
```

Tarih verilmezse `Europe/Istanbul` güncel tarihi kullanılır.

## GitHub Actions

Workflow `.github/workflows/python-rg.yml` dosyasındadır.

- Her gün `03:50 UTC` çalışır (`06:50 Europe/Istanbul`).
- Manuel çalıştırmada geçmiş tarih verilebilir.
- Pull requestlerde yalnız testler çalışır; dış kaynaklara istek gönderilmez.
- Scheduled/manual run çıktıları, başarısız run dahil, 14 gün GitHub artifact olarak tutulur.
