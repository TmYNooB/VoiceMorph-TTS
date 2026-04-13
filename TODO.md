# TODO – TmYNoobs VoiceMorph

## 🐛 Bugs / offene Punkte

### 1. Font "Segoe UI" fehlt auf macOS → 40ms Startup-Lag
**Fehlermeldung:**
```
qt.qpa.fonts: Populating font family aliases took 40 ms.
Replace uses of missing font family "Segoe UI" with one that exists to avoid this cost.
```
**Ursache:** `ui/styles.py` verwendet `"Segoe UI"` als Font-Family – diese existiert nur auf Windows.  
**Fix:** In `styles.py` Font-Stack auf macOS-kompatibel umstellen:
```css
font-family: "SF Pro Text", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
```
oder per `QFontDatabase` zur Laufzeit den besten verfügbaren Font wählen.

---

### 2. ~~`current_rms` AttributeError → App-Crash~~ ✅ behoben (13.04.2026)
**War:** `AudioEngine` hatte kein `current_rms`-Attribut nach letztem Refactoring.  
**Fix:** `self.current_rms: float = 0.0` in `__init__` wieder hinzugefügt.

---

## 💡 Ideen / Verbesserungen (nicht dringend)

- [ ] Manuelle Parameter-Slider in der UI (Pitch, Reverb, etc.) direkt einstellbar
- [ ] Latenz-Anzeige im Voice Tab ("~150 ms")
- [ ] Presets exportieren/importieren als ZIP
