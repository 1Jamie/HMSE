# 🧪 HMSE Validation and Experimental Methodology

## 1. Purpose and Scope

This document defines the **validation, testing, and evaluation methodology** for the **HyperDrive Microcontroller Storage Engine (HMSE)**.  
It establishes a formal process to empirically investigate the system's **compression performance**, **architectural correctness**, **resource efficiency**, and **practical viability** on microcontroller-class hardware (ESP32-S3).

**Primary Research Question:** Can useful compression ratios be achieved in very low-power environments (P < 1 W) using multi-layer data reduction?

**Formal Definitions:**
- **Compression Factor (CF)**: Ratio of input size to output size, CF = S_input / S_output (unitless)
- **Useful Compression**: CF ≥ 5:1 (defined below)
- **Low-Power Environment**: P_avg < 1.0 W sustained during compression operation
- **Multi-Layer Data Reduction**: Sequential application of L1 (lossless compression), L2 (content-defined chunking), L3 (exact deduplication), L4 (similarity-based delta encoding)

**Definition of "Useful Compression":** For this research, **useful compression** is formally defined as:

$$CF \geq 5.0 \text{ (compression factor 5:1 or greater)}$$

This threshold significantly exceeds typical single-pass algorithms (BZ2: ~3:1, zstd: ~3-4:1) and provides meaningful storage density improvements for embedded applications. This threshold also exceeds the baseline performance of space-grade compression standards such as [CCSDS 121.0-B-3](https://ccsds.org/wp-content/uploads/gravity_forms/5-448e85c647331d9cbaf66c096458bdd5/2025/01//121x0b3.pdf?gv-iframe=true), making HMSE potentially suitable for satellite and aerospace applications.

**Rationale for 5:1 Threshold:** This threshold represents the engineering trade-off point where storage density improvements and energy savings (transmission, storage costs, archival) begin to substantially outweigh the added implementation complexity and computational overhead of multi-layer processing in resource-constrained environments. Below 5:1, simpler single-pass algorithms provide better engineering economics.

**Validation Goal:** Measure the compression factors achievable through the L1-L4 pipeline on diverse text corpora, characterize power efficiency (MB compressed per watt), and determine whether MCU-based compression is **competitive in final compression ratio or superior in energy efficiency** compared to traditional algorithms (BZ2, zstd). Success is defined as achieving **CF ≥ 5:1 on ≥50% of tested corpora** (at least 2 out of 4: Wikipedia, News, GitHub, arXiv). Wikipedia provides an optimistic upper bound while arXiv provides a pessimistic lower bound.

### 1.3 Pre-registration and Transparency

This validation methodology was **pre-registered** before data collection to prevent p-hacking and HARKing (Hypothesizing After Results are Known).

**Pre-registration includes:**
- **Hypotheses**: H₀ (null) and H₁ (alternative) for primary and secondary tests
- **Sample sizes**: n = 30 runs per configuration per corpus (120 total runs minimum)
- **Stopping rules**: Fixed sample size (no optional stopping based on intermediate results)
- **Statistical tests**: Two-sample t-test (HMSE vs BZ2), one-sample t-test (HMSE vs 5:1 threshold), α = 0.05
- **Primary vs. exploratory analyses**: Primary = CF comparison, Exploratory = per-layer contribution analysis

**Deviations from plan:**
Any deviations from this methodology during execution will be documented in `VALIDATION_REPORT.md` with:
- Justification for deviation
- Impact on validity
- Corrective measures taken

**Open Science Commitment:**
- All raw data, scripts, and logs archived in `/validation/` directory
- Pre-registered plan available at: `[OSF/Zenodo DOI to be added]`
- Dataset mirrors archived at: `[Institutional repository URL]`
- Replication package: `[GitHub release URL]/validation/replication-package-v1.0.tar.gz`

---

## 2. Experimental Objectives

### 2.1 Primary Objectives
1. **Validate compression performance**
   - Confirm CF ≥ 5:1 on ≥50% of tested corpora (at least 2 out of 4)
   - Measure entropy reduction per layer (L1–L4) for each corpus

2. **Verify architectural correctness**
   - Confirm data integrity through reversible encoding/decoding cycles  
   - Verify that chunking, hashing, and deduplication layers produce consistent indices and deltas

3. **Assess hardware feasibility**
   - Ensure all layers execute within ESP32-S3 resource limits (PSRAM, flash, CPU)
   - Measure processing time and throughput for typical workloads

### 2.2 Secondary Objectives
1. Quantify **PSRAM utilization**, **I/O bandwidth**, and **energy consumption**
2. Evaluate **deduplication effectiveness** across corpus redundancy patterns
3. Identify **failure thresholds** (corpus size, entropy, fragmentation)
4. Benchmark performance vs. established compression baselines (e.g., BZ2, ZIM)

---

## 3. Experimental Setup

### 3.1 Hardware Environment

| Component | Specification | Unit Standard |
|------------|---------------|---------------|
| **MCU** | ESP32-S3 n16r8 (Dual Xtensa LX7, 240 MHz, 512 KiB SRAM + 8 MiB PSRAM) | Binary (KiB, MiB) for memory |
| **Input Storage** | 16 GB microSD (SDMMC interface, pre-loaded with test corpora) | Decimal (GB) per SD card spec |
| **Output Storage** | 8 GB microSD (SPI interface, receives compressed archive per test) | Decimal (GB) per SD card spec |
| **Power** | USB-C 5 V @ 500 mA max (P_max = 2.5 W), power logging via INA219 | Watts (W), Watt-hours (Wh) |
| **Firmware Framework** | ESP-IDF v5.3.0 (exact version TBD) + FreeRTOS kernel | — |
| **Interfaces Used** | SDMMC (input SD, 4-bit mode @ 40 MHz), SPI (output SD, 40 MHz), UART debug @ 115200 bps | — |
| **Compiler Flags** | `-O2`, `-ffast-math`, `-mlongcalls`, `-mfix-esp32-psram-cache-issue` | GCC 13.2.0 |

**Unit Conventions:**
- **Memory (SRAM, PSRAM)**: Binary units (KiB = 2^10 bytes, MiB = 2^20 bytes)
- **Storage (SD cards)**: Decimal units (GB = 10^9 bytes, per manufacturer specification)
- **Throughput**: MB/s = 10^6 bytes/second (decimal, matches SD card datasheets)
- **Energy**: Watt-hours (Wh), milliwatt-hours (mWh)
- **Power**: Watts (W), milliwatts (mW)

### 3.2 Software Stack
- HMSE firmware components:
  - **L1:** DEFLATE / zlib variant (1 MB PSRAM dictionary)
  - **L2:** FastCDC content-defined chunking
  - **L3:** SHA-256 hash indexing + exact deduplication table
  - **L4:** MinHash / LSH similarity delta encoding
- Logging via **UART 115200 bps**
- Benchmark scripts in **Python 3.11** for host-side reconstruction, timing, and verification

### 3.3 Reproducibility Requirements

**Software Versions (Exact Specifications for Reproducibility):**
- **ESP-IDF**: v5.3.0 (commit hash to be recorded pre-testing, format: `git rev-parse HEAD`)
- **Python**: 3.11.6 (for analysis scripts)
- **Toolchain**: `xtensa-esp32s3-elf-gcc` 13.2.0
- **Analysis Libraries**: `numpy` 1.24.0, `matplotlib` 3.7.0, `scipy` 1.10.0
- **Operating System (host)**: Ubuntu 22.04 LTS (kernel 5.15.0) for baseline BZ2 comparisons

**Random Seed Control:**

To ensure **bitwise reproducibility**, all random operations use fixed seeds:

| Operation | Seed | Implementation | Purpose |
|-----------|------|----------------|---------|
| **Dataset sampling** | `random.seed(42)` | Python `numpy.random` | Wikipedia article selection for subsets (1GB/5GB/10GB) |
| **Corpus subset generation** | `random.seed(42)` | Python `random` module | Random sampling for stratified test sets |
| **Chunk selection testing** | `0xDEADBEEF` | C `srand()` in firmware | PSRAM cache eviction testing, stress test selection |
| **MinHash permutations** | **Deterministic (not random)** | Seeds: `[1, 2, 3, ..., 128]` | Hash functions use sequential seeds for 128 permutations; no randomness required |
| **FastCDC boundaries** | **Content-defined (not random)** | Rabin fingerprint polynomial | Boundaries determined by content hash (H ≡ 0 mod P); fully deterministic given input |

**Verification:**
- All random operations logged to `validation/logs/random_operations.log`
- Rerunning with same seeds must produce identical chunk boundaries, compression ratios, and index sizes
- Python script `verify_determinism.py` confirms bitwise-identical outputs across runs

**Configuration Files:**
- `sdkconfig`: Archived in `/validation/config/sdkconfig.baseline`
- Compiler flags: `-O2 -ffast-math -DCONFIG_SPIRAM_SPEED_80M`
- All configuration files tagged with git commit SHA

**Data Provenance (Dataset Versioning):**

| Corpus | Source | Version/Date | SHA-256 Hash | Size | Download URL |
|--------|--------|--------------|--------------|------|--------------|
| **Wikipedia** | Wikimedia dumps | `enwiki-20251015-pages-articles.xml.bz2` | `[TBD pre-testing]` | 10 GB sample | `https://dumps.wikimedia.org/enwiki/20251015/` |
| **arXiv** | arXiv bulk data | Papers 2020-2024 bulk download | `[TBD pre-testing]` | 10 GB sample | `https://arxiv.org/help/bulk_data` |
| **News Articles** | Common Crawl | October 2025 snapshot | `[TBD pre-testing]` | 10 GB sample | `https://commoncrawl.org/` |
| **GitHub Code** | GH Archive | October 2025 snapshot, popular repos | `[TBD pre-testing]` | 10 GB sample | `https://www.gharchive.org/` |

**Versioning Requirements:**
- All corpus samples archived with SHA-256 checksums before testing
- Exact dataset versions documented in `/validation/datasets/MANIFEST.txt`
- Random sampling seeds recorded for reproducible subset generation

**Replication Package:**
Available at: `[repository URL]/validation/replication-package-v1.0.tar.gz`
- Contains: firmware source, datasets, scripts, configs, expected outputs

**Key Reproducibility Tools:**

1. **Energy Calculator (`tools/energy_calculator.py`)**:
   - Validates total system energy model (compression + transmission)
   - Calculates break-even compression factors for any bandwidth scenario
   - Generates energy vs. CF curves for visualization
   - Ensures theoretical claims (§5.7 energy analysis) are independently verifiable

2. **Docker Environment (`tools/Dockerfile` + `requirements.txt`)**:
   - Ensures bitwise-exact reproducibility of energy calculations
   - Pinned dependencies: `matplotlib>=3.7.0`, `numpy>=1.24.0`
   - Usage: `docker build -t hmse-tools tools/ && docker run --rm hmse-tools --size 75 --cf 9.375 --bandwidth 1 --transmit-power 5`
   - Eliminates "works on my machine" issues for validation reviewers

3. **Verification Scripts**:
   - `verify_determinism.py`: Confirms bitwise-identical outputs across runs with same seeds
   - `validate_energy_model.py`: Compares measured power (INA219) to theoretical projections

**Reproducibility Verification Procedure:**

To verify complete reproducibility:
```bash
# 1. Build Docker environment
cd tools/
docker build -t hmse-tools .

# 2. Run energy calculator with documented scenarios
docker run --rm hmse-tools --size 75 --cf 9.375 --bandwidth 1 --transmit-power 5 > energy_output.txt

# 3. Compare to expected output
diff energy_output.txt validation/expected_outputs/energy_satellite.txt

# 4. Verify firmware determinism
python validation/verify_determinism.py --config sdkconfig.baseline --runs 3

# 5. Expected result: All outputs match byte-for-byte
```

**Exit Criteria for Reproducibility**:
- ✅ Energy calculator produces identical results across systems (Docker ensures this)
- ✅ Firmware produces identical compression ratios (±0.01:1) with same seeds across 3 runs
- ✅ All SHA-256 checksums of outputs match documented expected values
- ✅ Independent reviewer can reproduce within 4 hours using provided package

---

## 4. Datasets

### 4.1 Primary Test Corpora (Equal Priority)

**Testing Approach:** Each corpus is tested in **separate compression runs** with full 8 GB output card available per test. This eliminates storage contention and provides clear per-corpus validation.

**⚠️ Critical Requirement:** To address selection bias and validate generalizability, the following diverse corpora are tested with **equal priority**:

| Corpus | Source | Size | Hypothesized CF | Redundancy Profile | Test Priority |
|--------|--------|------|-------------|-------------------|---------------|
| **Wikipedia** | `enwiki-20251015-pages-articles.xml.bz2` | October 15, 2025 | 10.0 | **8-10:1** (high) | Templates, infoboxes, citations | **Best-case benchmark** |
| **News Articles** | Common Crawl `CC-MAIN-2025-40` | October 2025 | 10.0 | **4-6:1** (medium) | Temporal redundancy, boilerplate | **Realistic case** |
| **GitHub Code** | GH Archive popular repos (stars > 1000) | October 2025 snapshot | 10.0 | **3-5:1** (medium) | Code redundancy (functions, imports) | **Code vs. text** |
| **arXiv Papers** | arXiv bulk data `cs.*`, `math.*` categories | Papers 2020-2024 | 10.0 | **2-3:1** (low) | Unique scientific notation | **Pessimistic case** |
| **Random Data** | `/dev/urandom` with seed 0xDEADBEEF | Generated pre-test | 1.0 | **1.0:1** (none) | Incompressible (entropy = 8.0 bits/byte) | **Worst-case baseline** |

**Sampling Methodology:**
- **Wikipedia**: Random stratified sample across all categories (seed: 42)
- **arXiv**: Most recent 10,000 papers from cs.* and math.* (sorted by date)
- **News**: Random 10,000 articles from Common Crawl (seed: 42)
- **GitHub**: Top 100 repos by stars (Python, JavaScript, C/C++), concatenated source files
- **Random**: Generated once, archived, reused for all tests (deterministic)

### 4.2 Success Criterion (Pre-Registered)

**Primary Success Criterion:** CF ≥ 5:1 on at least **2 out of 4 main corpora** (≥50%)

**Projected Outcomes** (if hypotheses hold):
- **Wikipedia**: 8.7:1 (✓ exceeds 5:1 threshold)
- **News**: 5:1 (✓ meets 5:1 threshold)
- **GitHub**: 4:1 (⚠️ below threshold, acceptable)
- **arXiv**: 2.5:1 (⚠️ below threshold, expected)
- **Expected result**: 2 out of 4 meet threshold = **SUCCESS**

**Rationale:** This criterion acknowledges that highly unique data types (scientific papers with unique notation) may not compress well, while still validating the approach on typical text corpora. The 50% threshold ensures generalizability beyond Wikipedia's optimistic characteristics.

**Reporting Requirement:**
- Report performance as **range** (min, median, max) across all corpora
- Explicitly label Wikipedia as "best-case: 8.7:1"
- Report median performance across diverse datasets as primary metric
- Success/failure determined by ≥50% criterion, not Wikipedia alone

### 4.3 Comparison Baselines
| Compression Method | Implementation | Reference |
|--------------------|----------------|------------|
| **BZ2** | bzip2 v1.0.8 | Wikipedia official |
| **ZIM** | Kiwix openzim | Wikipedia offline standard |
| **zstd -19** | Facebook Zstandard | High-performance reference |
| **CCSDS 121.0-B-3** | Space-grade lossless compression | [CCSDS Standard](https://ccsds.org/wp-content/uploads/gravity_forms/5-448e85c647331d9cbaf66c096458bdd5/2025/01//121x0b3.pdf?gv-iframe=true) |

---

## 5. Evaluation Metrics

| Category | Metric | Formal Definition | Unit | Measurement Method |
|-----------|---------|-------------------|------|-------------------|
| **Compression** | **Total compression factor (CF)** | $CF = \frac{S_{input}}{S_{output}}$ | Unitless ratio | File size comparison (bytes) |
| | **Per-layer gain** | $CF_i = \frac{S_{in,i}}{S_{out,i}}$ for layer i | Unitless ratio | Per-layer output measurement |
| **Integrity** | **Reconstruction fidelity** | $\text{SHA-256}(D(C(x))) = \text{SHA-256}(x)$ | Boolean (pass/fail) | Cryptographic hash comparison |
| **Performance** | **Batch processing speed** | $v = \frac{S_{processed}}{t_{elapsed}}$ | MB/s (10^6 bytes/s) | SDMMC/timer measurements |
| | **Total batch completion time** | $T_{batch} = \frac{S_{corpus}}{v_{avg}}$ | Hours (h) | Wall-clock time per 10 GB corpus |
| **Resource Usage** | **PSRAM usage** | $M_{peak} = \max(M(t))$ | MiB (2^20 bytes) | `heap_caps_get_free_size()` |
| | **Flash I/O throughput** | $v_{IO} = \frac{B_{transferred}}{t_{elapsed}}$ | MB/s (10^6 bytes/s) | SDMMC driver metrics |
| **Power** | **Average power consumed** | $P_{avg} = \frac{1}{T}\int_0^T P(t) dt$ | Watts (W) | INA219 @ 10 Hz over 60s windows |
| **Deduplication** | **Unique chunk ratio** | $R_{unique} = \frac{N_{unique}}{N_{total}}$ | Percentage (%) | Hash table entry count |
| | **Similarity hit rate** | $R_{LSH} = \frac{N_{LSH\ matches}}{N_{candidate\ pairs}}$ | Percentage (%) | LSH collision count / probes |

---

### 5.4 Energy Efficiency Metrics

To validate the energy break-even analysis (README.md §5.7), the following energy metrics must be measured:

| Metric | Formal Definition | Measurement Method | Target | Unit | Purpose |
|--------|-------------------|-------------------|--------|------|---------|
| **Compression power** | $P_{avg} = \frac{1}{T}\int_0^T P(t) dt$ | INA219 @ 10 Hz sampling | 0.5 W ± 0.05 W | Watts (W) | Validate power budget assumption |
| **Compression energy** | $E = \int_0^T P(t) \, dt$ | Integrate power over batch | 2.5 Wh (10 GB corpus) | Watt-hours (Wh) | Total energy cost per corpus |
| **Energy per GB** | $\eta = \frac{E_{\text{compress}}}{S_{\text{input}}}$ | $E$ / input size | 0.25 Wh/GB | Wh/GB | Efficiency metric |
| **Break-even CF** | $CF_{min} = \frac{E_{tx,uncompressed}}{E_{tx,uncompressed} - E_{compress}}$ | Using measured $P_{\text{compress}}$ | ~1.02:1 (1 Mbps) | Unitless | Validate theoretical model |
| **ROI (measured)** | $ROI = \frac{E_{\text{saved}}}{E_{\text{compress}}}$ | Energy savings / compression cost | ≥ 35× @ CF=5:1 | Unitless | Validate threshold justification |

**Validation Test (6-Hour Continuous Run):**

**Procedure:**
1. Instrument ESP32-S3 with INA219 current sensor on VDD rail
2. Configure INA219: 16V range, 0.1Ω shunt, 12-bit ADC
3. Log power measurements every 100 ms over 6-hour compression test
4. Process ~10 GB corpus during test (one full corpus, validates sustained operation)

**Data Analysis:**
```python
import numpy as np

# Load power measurements
power_samples = np.loadtxt('power_log.csv')  # Watts

# Calculate statistics
mean_power = np.mean(power_samples)
std_power = np.std(power_samples)
total_energy = np.trapz(power_samples, dx=0.1/3600)  # Wh (100ms sampling)

# Energy per GB
energy_per_gb = total_energy / data_processed_gb

print(f"Mean Power: {mean_power:.3f} W ± {std_power:.3f} W")
print(f"Total Energy: {total_energy:.2f} Wh")
print(f"Energy/GB: {energy_per_gb:.3f} Wh/GB")
```

**Acceptance Criteria:**
- **Mean power**: 0.4-0.6 W (±20% tolerance from 0.5W projection)
- **Energy per GB**: 0.20-0.30 Wh/GB (validates linear scaling)
- **Break-even CF (measured)**: 0.9-1.2:1 vs. theoretical 1.022:1 (±20% tolerance)
- **Power stability**: σ/μ < 0.15 (coefficient of variation < 15%)

**Comparison to Theoretical Model:**

Using measured power $P_{\text{measured}}$, recalculate break-even CF:

$$CF_{\text{min,measured}} = \frac{E_{\text{transmit,uncompressed}}}{E_{\text{transmit,uncompressed}} - P_{\text{measured}} \times T_{\text{compress}}}$$

Compare to theoretical $CF_{\min} = 1.022$ (1 Mbps satellite scenario). If measured CF is within ±20%, theoretical model is validated.

**Energy ROI Validation:**

For 5:1 compression factor, calculate measured ROI:

$$ROI_{\text{measured}} = \frac{E_{\text{transmit}}(CF=1) - E_{\text{transmit}}(CF=5)}{E_{\text{compress,measured}}}$$

Expected: ROI ≥ 30× (allowing margin for measurement error vs. theoretical 36×)

---

### 5.5 Statistical Analysis Framework

**Hypothesis Testing:**

**Primary Hypothesis (Two-Tailed):**
- **H₀**: μ_CF = 3.0 (HMSE performs equivalently to BZ2 baseline)
- **H₁**: μ_CF ≠ 3.0 (HMSE differs from baseline)
- **Significance level**: α = 0.05
- **Statistical test**: Two-sample t-test (HMSE vs. BZ2)

**Secondary Hypothesis (One-Tailed, if H₁ confirmed):**
- **H₀**: μ_CF ≤ 5.0 (Below operational threshold)
- **H₁**: μ_CF > 5.0 (Exceeds operational threshold)
- **Significance level**: α = 0.05

**Sample Size and Power Analysis (Corrected):**
- **Minimum trials per dataset**: n = 30 runs
- **Power (1-β)**: 0.80 (80% probability to detect true effect)
- **Minimum Detectable Effect Size (MDES)**: 
  - Calculated (not assumed): MDES = t_(critical) × σ / √n
  - For n=30, α=0.05, two-tailed: MDES ≈ **0.52** (Cohen's d)
  - **Interpretation**: Study can detect CF differences ≥ 0.5:1 with 80% confidence
  - **Limitation**: Improvements smaller than 0.5:1 (e.g., 5.2:1 vs. 5.5:1) may not reach statistical significance

**Implication:** The study is **not powered** to detect small incremental improvements. It can only distinguish between "substantially better" (CF > 5.5:1) vs. "marginally better" (CF ≈ 5:1) with low confidence.

**Confidence Intervals:**
- Report 95% CI for all compression factor measurements
- Bootstrap resampling (B=1000) for non-normal distributions

**Measurement Precision:**

| Metric | Precision | Instrument | Calibration |
|--------|-----------|------------|-------------|
| Compression Factor | ±0.1:1 | File size comparison | N/A |
| Throughput | ±5% | `esp_timer_get_time()` | System clock verified |
| Power | ±0.01 W | INA219 | Factory calibrated |
| Latency | ±10 µs | Hardware timer | Crystal oscillator 40 MHz ±20 ppm |

### 5.6 Measurement Error and Uncertainty

| Metric | Systematic Error | Random Error | Mitigation |
|--------|------------------|--------------|------------|
| **File size** | ±0 bytes | N/A | Direct filesystem query |
| **Timer (latency)** | ±20 µs (clock drift) | ±5 µs | Use `esp_timer_get_time()` |
| **Power (INA219)** | ±0.5% FS (±2.5 mW) | ±0.1 mW | Average over 60s windows |
| **PSRAM usage** | ±4 KB (allocator) | N/A | Call `heap_caps_get_free_size()` |

**Error Propagation:**
For derived metrics (e.g., MB/s = bytes / time):
- Throughput error: δT = T × √[(δB/B)² + (δt/t)²]
- Report all derived metrics with propagated uncertainty

---

## 6. Validation Procedure

**Critical Path to Success:**

While this validation plan is comprehensive, the **critical path** to demonstrating success involves testing all four primary corpora:

1. **Execute the "Full Pipeline" ablation study** (§6.5) on all four 10 GB corpora (Wikipedia, News, GitHub, arXiv) to measure compression factors with all layers active (L1+L2+L3+L4)
2. **Determine success/failure** based on how many corpora achieve CF ≥ 5:1

**Success Criterion:** If at least **2 out of 4 corpora** achieve mean CF ≥ 5:1 (with p < 0.05 via one-sample t-test, n=30 trials per corpus), the **primary research goal will have been met**, demonstrating that useful compression can be achieved in very low-power environments across diverse data types.

**Secondary validations** (functional correctness, comparative baselines, stress testing, energy measurements) provide important characterization data but are not required to answer the core research question.

**This focus ensures:**
- Resources prioritized on the most critical measurement
- Clear success/failure determination
- Rapid initial validation before extended testing

---

### 6.1 Functional Validation
1. Encode → Decode loop with checksum verification (SHA-256 end-to-end)  
2. Validate per-layer checkpoints (L1→L2→L3→L4) for lossless behavior  
3. Confirm chunk boundaries and indices persist across re-runs  

### 6.2 Performance Validation
1. Process each dataset subset sequentially  
2. Record timing and throughput via internal log timestamps  
3. Measure PSRAM and flash usage at each stage  

### 6.3 Comparative Validation
1. Compress the same corpus using BZ2, ZIM, and zstd on host system  
2. Compare resulting compression factors and reconstruction integrity  
3. Evaluate energy efficiency (MB/J) and throughput vs. reference systems

#### 6.3.1 Fair Comparison Protocol

**Objective:** Ensure baseline comparisons (BZ2, ZIM, zstd) use equivalent configurations.

| Baseline | Configuration | Justification |
|----------|---------------|---------------|
| **bzip2** | Default (`-9`) | Wikipedia official compression |
| **zstd** | Level 19 | Comparable compression ratio to BZ2 |
| **ZIM (Kiwix)** | Default | Wikipedia offline standard |

**Controlled Variables:**
- All methods process **same input**: Decompressed Wikipedia XML (not BZ2 file)
- Same hardware for baseline tests: x86-64, 16 GB RAM, Ubuntu 22.04
- Exclude index overhead from all methods (compare payload only)
- Report both "standalone" and "with index" sizes for fairness

**Measurement Protocol:**
1. Decompress Wikipedia dump: `bzip2 -d enwiki.xml.bz2`
2. Compress with each method: `time [method] < input.xml > output.[ext]`
3. Record: wall-clock time, final size, peak memory usage
4. Compute CF = Input size / Output size (payload only)

**Acknowledgment:**
- HMSE includes deduplication indices (5.6% overhead)
- Baseline comparisons adjusted to include equivalent index sizes
- Report both "raw" and "fair" (index-inclusive) compression factors

### 6.4 Stress Testing
1. Push input corpus size until failure or resource exhaustion  
2. Record entropy threshold where pipeline breakdown occurs  
3. Identify memory fragmentation or task starvation events in FreeRTOS logs

### 6.5 Ablation Studies

**Objective:** Isolate the contribution of each layer to overall compression.

| Configuration | L1 | L2 | L3 | L4 | Hypothesized CF | Purpose |
|---------------|----|----|----|----|-------------|---------|
| **Baseline** | ✓ | ✗ | ✗ | ✗ | 3:1 | Isolate L1 (DEFLATE) contribution (plausible based on DEFLATE benchmarks) |
| **+CDC** | ✓ | ✓ | ✗ | ✗ | 3:1 | Verify CDC doesn't change CF (boundary detection only) |
| **+Dedupe** | ✓ | ✓ | ✓ | ✗ | 5-7:1 | Isolate L3 (exact dedupe) contribution (corpus-dependent) |
| **Full Pipeline** | ✓ | ✓ | ✓ | ✓ | 2.5-9:1 (corpus-dependent) | Complete system (range: arXiv 2.5:1 to Wikipedia 8.7:1) |
| **L4 Only** | ✗ | ✓ | ✗ | ✓ | 1.5-2:1 | Isolate L4 (similarity) contribution (highly variable) |

**Analysis:**
- For each configuration, run on all four 10 GB corpora (n=10 trials per corpus)
- Measure mean CF and 95% CI for each corpus
- Compute statistical significance of each layer's contribution (paired t-test)
- Report per-corpus results: "L3 contributes Δ = 2.1 ± 0.3:1 on Wikipedia (p < 0.001)"
- Report range across corpora: "L3 contribution ranges from 1.2:1 (arXiv) to 3:1 (Wikipedia)"

---

## 7. Success Criteria

| Tier | Multi-Corpus Criterion | Description | Success Definition |
|------|------------------------|-------------|-------------------|
| **Tier 4 (Full)** | ≥ 3/4 corpora ≥ 5:1 | Strong generalization | All except arXiv meet threshold |
| **Tier 3 (Target)** | ≥ 2/4 corpora ≥ 5:1 | **Primary success criterion** | Validates approach across diverse data |
| **Tier 2 (Partial)** | 1/4 corpus ≥ 5:1 | Limited validation | Proves concept on one corpus type |
| **Tier 1 (Marginal)** | All corpora 3-5:1 | Better than BZ2 | Shows improvement but not useful threshold |
| **Tier 0 (Failure)** | All corpora < 3:1 | Below BZ2 baseline | No advantage over traditional compression |

---

## 8. Risk and Contingency Plan

| Risk | Mitigation Strategy |
|-------|----------------------|
| **Insufficient compression (< 5:1)** | Optimize L3 hash tables; expand PSRAM index; test delta encoding |
| **Excessive latency** | Implement task-level parallelism; offload I/O to second core |
| **PSRAM fragmentation** | Use static buffers and pooled allocation |
| **Flash wear-leveling degradation** | Enable SDMMC wear-leveling; maintain write journals |
| **Entropy mismatch (non-redundant data)** | Substitute corpus with higher redundancy subset for validation |
| **Thermal or power limits** | Limit duty cycle, add temperature telemetry |

### 8.5 Threats to Validity

#### Internal Validity (Can we trust the causal claims?)

| Threat | Mitigation |
|--------|------------|
| **Instrumentation effects** | Use calibrated INA219; verify timer accuracy with oscilloscope |
| **History effects** | Control for thermal throttling (monitor ESP32-S3 temperature) |
| **Selection bias** | Use stratified random sampling for Wikipedia subsets |
| **Implementation artifacts** | Compare against reference implementations (zlib, bzip2) |

#### External Validity (Can results generalize?)

| Threat | Mitigation |
|--------|------------|
| **Corpus selection bias (CRITICAL)** | **Wikipedia exhibits optimal characteristics for deduplication** (high structural redundancy, templates, standardized formatting). This is a **best-case scenario** that may not generalize. **Required**: Test on diverse corpora with varying redundancy profiles: <br>1. **arXiv papers** (low redundancy, unique scientific notation)<br>2. **GitHub repositories** (code vs. text comparison)<br>3. **News articles** (temporal redundancy, current events)<br>4. **Synthetic random data** (worst-case baseline, ~1.0:1 CF)<br>**Report performance range** (min, median, max) across corpora and acknowledge Wikipedia as optimistic. |
| **Hardware specificity** | Acknowledge results specific to ESP32-S3; discuss ARM Cortex-M7 comparison |
| **Wikipedia version drift** | Document exact dump version; archive dataset for replication |
| **Workload realism** | Justify Wikipedia as representative of structured text corpora (**with caveat** that other text types may perform worse) |

#### Construct Validity (Are we measuring what we claim?)

| Threat | Mitigation |
|--------|------------|
| **Compression factor definition** | Clearly define: Input (decompressed) / Output (physical storage) |
| **Throughput measurement** | Exclude I/O wait time; measure only CPU processing time |
| **Deduplication rate** | Distinguish "exact duplicate" from "similar" chunks |

#### Conclusion Validity (Are statistical inferences sound?)

| Threat | Mitigation |
|--------|------------|
| **Low statistical power** | Require n ≥ 30 trials per configuration |
| **Multiple comparisons** | Apply Bonferroni correction when comparing >2 configurations |
| **Outlier sensitivity** | Report both mean and median; use robust statistics |

---

## 9. Data Collection and Analysis Plan

### 9.1 Primary Analysis
- **Compression factor distribution**: Test for normality (Shapiro-Wilk)
- **Central tendency**: Report mean, median, mode with 95% CI
- **Variability**: Report standard deviation, IQR, coefficient of variation

### 9.2 Hypothesis Testing

```python
# Example: Test if HMSE CF > 5:1 (operational threshold)
from scipy import stats
cf_samples = [5.2, 5.8, 6.1, ...]  # n=30 trials
t_stat, p_value = stats.ttest_1samp(cf_samples, popmean=5.0, alternative='greater')
print(f"t={t_stat:.3f}, p={p_value:.4f}")
# Decision: Reject H₀ if p < 0.05
```

### 9.3 Effect Size Reporting
- Cohen's d for compression factor improvements
- η² (eta squared) for layer contribution in ablation studies

### 9.4 Regression Analysis
- Model: `CF ~ L3_dedupe_rate + L4_similarity_rate + corpus_entropy`
- Identify which factors most strongly predict compression success
- Report R², adjusted R², F-statistic

### 9.5 Sensitivity Analysis
- Vary key parameters (±20%): PSRAM size, chunk size, LSH bands
- Measure impact on CF and throughput
- Identify brittle vs. robust design choices

### 9.6 Data Visualization
- All benchmark logs exported as `.csv` (timestamped metrics)
- Compression results parsed with Python analysis scripts
- Generate plots:
  - Mean, median, and σ for compression factors
  - Power vs. throughput trade-off plots
  - Layer contribution charts (L1–L4 gain)
  - Box plots showing CF distribution by configuration
- Visualize results via matplotlib for inclusion in report or publication

---

## 10. Expected Outcomes

| Category | Anticipated Range | Interpretation |
|-----------|------------------|----------------|
| **Compression Factor** | 5–9.4 : 1 | Meets operational threshold–target range |
| **PSRAM Utilization** | ≤ 7 MB peak | Within ESP32-S3 limits |
| **Throughput** | 200–500 KB/s | Practical for offline corpus storage |
| **Power Draw** | ≤ 0.5 W avg | Sub-watt operation feasible |
| **Integrity** | 100% lossless reconstruction | Required for acceptance |

---

## 11. Reporting and Publication

All validation data, firmware binaries, and analysis scripts will be published in the repository under the **`/validation/`** directory and made available for independent replication.

Upon completion, results will be compiled into a companion paper:

> *“Empirical Validation of the HyperDrive Microcontroller Storage Engine: A Multi-Layer Deduplication Architecture on the ESP32-S3.”*

This will include quantitative results, performance curves, and a discussion of any observed divergence from the modeled compression ratios.

---

## 12. Conclusion

This validation plan defines a complete, reproducible framework for evaluating the HMSE system across performance, correctness, and efficiency dimensions.  
Successful execution of this plan will establish the **first empirical benchmark** of a **multi-layer deduplication pipeline** on microcontroller-class hardware, bridging the gap between theoretical storage-density models and real embedded implementations.

---

## 13. Peer Review Preparation Checklist

For submission to conferences/journals, ensure validation addresses:

**Experimental Design:**
- [ ] Hypotheses stated before data collection
- [ ] Sample sizes justified (power analysis)
- [ ] Control conditions defined
- [ ] Randomization procedure documented

**Statistical Rigor:**
- [ ] Significance tests specified (α = 0.05)
- [ ] Confidence intervals reported
- [ ] Effect sizes computed
- [ ] Multiple comparison corrections applied

**Reproducibility:**
- [ ] Software versions documented
- [ ] Random seeds specified
- [ ] Configuration files archived
- [ ] Replication package available

**Validity:**
- [ ] Threats to validity addressed
- [ ] Baseline fairness ensured
- [ ] Measurement error quantified
- [ ] Generalizability discussed

**Reporting:**
- [ ] Negative results included
- [ ] Outliers documented (not removed arbitrarily)
- [ ] Assumptions validated (e.g., normality)
- [ ] Limitations acknowledged

---

## 🧰 Implementation Checklist

This checklist defines the **step-by-step process** to execute the HMSE validation plan.

### A. Firmware Setup
- [ ] Install **ESP-IDF v5.3** and required toolchain  
- [ ] Clone HMSE repository  
- [ ] Configure `sdkconfig` for PSRAM and SDMMC support  
- [ ] Flash firmware via `idf.py flash`  
- [ ] Verify UART logging at `115200 bps`  

### B. Dataset Preparation
- [ ] Download `enwiki-latest-pages-articles.xml.bz2`  
- [ ] Extract and create **1 GB**, **5 GB**, and **10 GB** subsets  
- [ ] Copy datasets to microSD under `/hmse/input/`  

### C. Validation Execution
- [ ] Insert SD card and boot HMSE device  
- [ ] Run `hmse_validate()` command via serial interface  
- [ ] Capture UART log to file (`hmse_run_YYYYMMDD.log`)  
- [ ] Repeat for all dataset subsets  

### D. Data Collection
- [ ] Export `.csv` logs from HMSE firmware  
- [ ] Run Python analysis scripts (`analyze_results.py`)  
- [ ] Generate plots:
  - Compression factor by layer  
  - Throughput vs. power  
  - Unique chunk ratio  

### E. Comparative Testing
- [ ] Compress same datasets using:
  - `bzip2`
  - `zstd -19`
  - `zimwriterfs`  
- [ ] Record resulting sizes and compute ratios  

### F. Reporting
- [ ] Summarize results into `VALIDATION_REPORT.md`  
- [ ] Include power/throughput charts and summary tables  
- [ ] Tag release as `v0.9-validation`  

---

✅ **Deliverable Summary**
| Deliverable | Location | Description |
|--------------|-----------|--------------|
| **HMSE firmware binary** | `/firmware/` | Built ESP-IDF project |
| **Benchmark logs** | `/validation/logs/` | Raw UART outputs |
| **Processed CSV data** | `/validation/data/` | Parsed metrics |
| **Plots and charts** | `/validation/results/` | Graphical summaries |
| **Final report** | `/validation/VALIDATION_REPORT.md` | Human-readable results summary |

---

**Document Version:** 1.3  
**Last Updated:** October 20, 2025  
**Platform:** ESP32-S3 (Dual-core Xtensa LX7)  
**Changelog:**
- **v1.3 (Oct 20):** **Architectural update, multi-corpus validation framework & research refinement:**
  - **Terminology change**: Reworded to use 'operational threshold' instead of "mvp"
  - **Research Question**: Reframed to "Can useful compression ratios be achieved in very low-power environments (<1W)?"; defined useful as CF ≥ 5:1 (exceeds BZ2, potential CCSDS 121.0-B-3 compliance)
  - **Testing Paradigm**: Shifted from Wikipedia-centric to **diverse corpus testing** (4 × 10 GB samples: Wikipedia, arXiv, News, GitHub) tested in **separate runs**
  - **Success Criterion**: Changed to **"CF ≥ 5:1 on ≥50% of corpora"** (at least 2 out of 4), addressing selection bias; promoted diverse corpora to primary test set (Section 4.1)
  - **Hardware**: Updated to dual-SD (16 GB SDMMC input + 8 GB SPI output reused between tests); removed USB interface
  - **Metrics**: Redefined throughput as "batch processing speed" (determines completion time, not feasibility); emphasized power efficiency (MB/watt)
  - **Validation**: Critical path redefined (test all 4 corpora separately, not just Wikipedia + 1 diverse); expanded random seed documentation; reproducibility verification procedure
  - **Tier System**: Updated success criteria from Wikipedia-coverage tiers to multi-corpus tiers (Tier 3 = ≥2/4 corpora ≥5:1)
  - **Terminology**: Standardized "Hypothesized CF" (model-based) vs measured (empirical); Full Pipeline now shows 2.5-9:1 corpus-dependent range
- **v1.2 (Oct 19):** **Scientific rigor & validation framework:**
  - **Statistical Framework**: Added hypothesis testing (two-tailed primary, one-tailed secondary), power analysis (MDES = 0.52), confidence intervals (95% CI), measurement error quantification (±0.1:1 CF, ±5% throughput)
  - **Reproducibility**: Pre-registration (OSF/AsPredicted), software versions, random seed control, Docker replication package, data provenance tracking
  - **Corpus Diversity**: Added arXiv (low redundancy), GitHub (code), news articles, random data to prevent Wikipedia selection bias; performance reported as range (min/median/max)
  - **Analysis**: Ablation studies (5 configs), fair comparison protocol, threats to validity (internal/external/construct/conclusion), normality testing, effect size reporting, sensitivity analysis
  - **Peer Review**: Comprehensive checklist for publication readiness; prevents p-hacking and HARKing
- **v1.0 (Oct 17):** Initial validation methodology: experimental objectives, hardware/software setup (ESP-IDF v5.3), datasets (Wikipedia subsets), evaluation metrics, validation procedures, risk mitigation, reporting framework.

---
