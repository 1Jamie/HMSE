# HMSE Tools

Utility scripts for HMSE analysis and validation.

## Energy Calculator

`energy_calculator.py` - Calculates total system energy (compression + transmission) and determines break-even compression factors for different bandwidth scenarios.

### Installation

**Option 1: Docker (Recommended for Reproducibility)**

```bash
# Build container (one-time setup)
cd tools/
docker build -t hmse-tools .

# Run calculator
docker run --rm -v $(pwd):/data hmse-tools \
    --size 75 --cf 9.375 --bandwidth 1 --transmit-power 5

# Generate plot (output saved to current directory)
docker run --rm -v $(pwd):/data hmse-tools \
    --size 75 --cf 9.375 --bandwidth 1 --transmit-power 5 --plot
```

**Option 2: Local Python**

```bash
# Install dependencies
pip install -r requirements.txt

# Run calculator
python energy_calculator.py --size 75 --cf 9.375 --bandwidth 1 --transmit-power 5
```

---

### Usage

**Basic calculation (no plot):**
```bash
python energy_calculator.py --size 75 --cf 9.375 --bandwidth 1 --transmit-power 5
```

**Generate energy curve plot:**
```bash
python energy_calculator.py --size 75 --cf 9.375 --bandwidth 1 --transmit-power 5 --plot
```

**Custom compression parameters:**
```bash
python energy_calculator.py --size 75 --cf 5.0 --bandwidth 0.05 \
    --transmit-power 0.5 --compress-power 0.5 --compress-time 36
```

### Example Output

```
======================================================================
  HMSE Energy Analysis
======================================================================

📊 Scenario Parameters:
  Corpus Size:          75 GB
  Compression Factor:   9.375:1
  Transmission BW:      1 Mbps
  Transmit Power:       5 W
  Compress Power:       0.5 W
  Compress Time:        36 hours

⚡ Energy Breakdown (WITH Compression):
  Compression Energy:   18.0 Wh
  Transmission Energy:  88.9 Wh
  Total Energy:         106.9 Wh
  Transmission Time:    17.78 hours

⚡ Energy (NO Compression, CF=1.0):
  Transmission Energy:  833.3 Wh
  Total Energy:         833.3 Wh

💰 Energy Economics:
  Break-even CF:        1.022:1
  Safety Margin:        9.17×
  Energy Saved:         726.4 Wh (87.2%)
  Energy ROI:           40.4× (every 1 Wh spent saves 40.4 Wh)

💡 Interpretation:
  ✅ Compression is energy-positive with 9.2× safety margin
  ✅ ROI ≥ 36×: Multi-layer complexity justified

======================================================================
```

### Scenarios

**LEO Satellite (1 Mbps):**
```bash
python energy_calculator.py --size 75 --cf 9.375 --bandwidth 1 --transmit-power 5
# Break-even: 1.022:1, ROI: 40×
```

**LoRaWAN (50 kbps):**
```bash
python energy_calculator.py --size 75 --cf 5.0 --bandwidth 0.05 --transmit-power 0.5
# Break-even: 1.23:1, ROI: ~20×
```

**4G LTE (10 Mbps):**
```bash
python energy_calculator.py --size 75 --cf 3.0 --bandwidth 10 --transmit-power 2
# Break-even: 1.002:1, ROI: ~9000× (overkill)
```

### Interpretation

- **CF_min (Break-even)**: Minimum compression factor where total energy (compression + transmission) equals transmission-only energy
- **Safety Margin**: How much headroom exists above break-even (CF_actual / CF_min)
- **ROI**: Energy return on investment - how many Wh saved per 1 Wh spent on compression
- **Threshold**: ROI ≥ 36× justifies multi-layer complexity (CF ≥ 5:1 for typical satellite scenarios)

### Plot Output

When `--plot` is specified, generates `energy_curve.png` showing:
- Total energy vs. compression factor
- Break-even point (where compression = no compression)
- 5:1 "useful" threshold
- Compression energy (constant) vs. transmission energy (decreases with CF)

Example plot interpretation:
- **Flat region**: High CF → Transmission energy dominates (compression time negligible)
- **Steep region**: Low CF → Compression overhead significant
- **Break-even**: Where curves intersect (CF_min)

