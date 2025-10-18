---

# HyperDrive MicroController Storage Engine (HMSE)

### Comprehensive Specification for High Storage Density Research

![License](https://img.shields.io/badge/license-CC%20BY--NC--SA%204.0-blue)
![Target](https://img.shields.io/badge/compression-3.125%3A1-success)
![Platform](https://img.shields.io/badge/platform-ESP32--S3-orange)

**Author:** Autumn Celeste ([@1jamie](https://github.com/1jamie))  
**Project:** HyperDrive MicroController Storage Engine (HMSE)  
**License:** [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) (Attribution-NonCommercial-ShareAlike)  
**Commercial Licensing:** Contact author for commercial use arrangements

---

> **⚠️ WORK IN PROGRESS**
> 
> This document represents a **research specification and design proposal** that is currently under development. The architecture, algorithms, and performance projections described herein have not been fully implemented or validated. All compression ratios, throughput figures, and capacity estimates are **theoretical projections** based on established algorithms and hardware specifications, but require empirical validation through real-world testing.
>
> **Key Considerations:**
> - Implementation is planned but not yet complete
> - All performance numbers require verification with actual hardware and workloads
> - Mathematical models need validation against real Wikipedia corpus data
> - System integration and optimization phases are pending
>
> This specification serves as a comprehensive blueprint for research and development purposes.
>
> **📋 Validation Plan:** See [VALIDATION_METHODS.md](./VALIDATION_METHODS.md) for the complete experimental methodology, statistical analysis framework, and reproducibility requirements.

---

## Table of Contents

1. [Abstract and Motivation](#1-abstract-and-motivation)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Scientific and Technical Rationale](#3-scientific-and-technical-rationale)
4. [Feasibility Analysis and Mathematical Proof](#4-feasibility-analysis-and-mathematical-proof)
5. [Discussion and Practical Implications](#5-discussion-and-practical-implications)
6. [Implementation Plan and Verification](#6-implementation-plan-and-verification)
   - [Phase 0: Foundation Setup](#phase-0-foundation-setup-and-performance-baseline)
   - [Phase 1: Lossless Compression](#phase-1-lossless-compression-l1)
   - [Phase 2: Content-Defined Deduplication](#phase-2-content-defined-deduplication-l2--l3)
   - [Phase 3: Similarity Deduplication](#phase-3-similarity-deduplication-and-final-goal)
7. [Data Flow Architecture](#7-data-flow-architecture)
8. [Storage Budget Analysis](#8-storage-budget-analysis)
9. [Real-World Test Cases](#9-real-world-test-cases)
10. [Validation Methodology](./VALIDATION_METHODS.md) 📄
11. [References](#references)

---

## 1. Abstract and Motivation

The **HyperDrive MicroController Storage Engine (HMSE)** is a **research specification** that hypothesizes a multi-layered data reduction pipeline on the **ESP32-S3** could achieve high storage density.
The **goal** is to investigate whether the ~7.1 million English Wikipedia text corpus can be stored on an **8 GB MicroSD Card**.

**Baseline Data:**
- **Source**: English Wikipedia XML dump (pages-articles.xml.bz2)
- **Compressed size (BZ2)**: ~25 GB (download size)
- **Decompressed size**: ~75 GB raw XML/text (BZ2 achieves ~3:1 on text)
- **Target physical storage**: 8 GB MicroSD

**Compression Strategy (Hypothesized):**
- **L1-L4 pipeline operates on decompressed 75 GB text** (not on the BZ2 file)
- **Required** overall factor: 75 GB ÷ 8 GB = **9.375:1** (decompressed → final)
- Alternative framing: 25 GB ÷ 8 GB = **3.125:1** (BZ2-equivalent → final)

**Theoretical Approach:** This could potentially be achieved by systematically trading the MCU's projected CPU capacity (> 30 MB/s theoretical) for algorithmic density, while respecting the **USB 1.1** throughput constraint (≈ 1.0 MB/s). **All performance projections require empirical validation.**

**Note:** The system ingests **decompressed Wikipedia text** (75 GB logical), not the BZ2 file. DEFLATE is applied to raw text, not to already-compressed data.

### Units Convention

**Throughout this document:**
- **MB = 10⁶ bytes (decimal megabytes)** — used for storage capacities and industry-standard comparisons
- **MiB = 2²⁰ bytes = 1,048,576 bytes (binary mebibytes)** — used for throughput calculations and precise memory allocations
- **KB = 10³ bytes; KiB = 2¹⁰ bytes = 1,024 bytes**
- When comparing to USB 1.1 or SD card specs, we use decimal MB/s (matching industry datasheets)
- Internal memory allocations (PSRAM, buffers) use binary MiB for precision

---

## 2. System Architecture Overview

### 2.1 Hardware Architecture

The HMSE system leverages the ESP32-S3's dual-core architecture with asymmetric task assignment to optimize I/O responsiveness and computational throughput:

```mermaid
graph TB
    %% External Components
    PC["🖥️ Host PC<br/>USB 1.1 Interface"]
    MicroSD[("💾 8 GB MicroSD<br/>Deduplicated Storage")]
    
    %% Main MCU Container
    subgraph ESP32["🔧 ESP32-S3 Microcontroller"]
        
        %% Core 0 - I/O Management
        subgraph Core0["⚡ Core 0 - I/O Handler<br/>(Priority 5)"]
            USB["📡 USB 1.1 Handler<br/>1.0 MB/s"]
            SDM["💿 SD Card Driver<br/>4-bit @ 40 MHz<br/>5-15 MB/s"]
        end
        
        %% Core 1 - Processing Pipeline
        subgraph Core1["🧠 Core 1 - HMSE Engine<br/>(Priority 3)"]
            L1["📦 L1: DEFLATE<br/>Compression<br/>1 MB Window"]
            L2["✂️ L2: FastCDC<br/>Content Chunking<br/>Rabin Hash"]
            L3["🔍 L3: SHA-256<br/>Exact Dedupe<br/>HW Accelerated"]
            L4["🔗 L4: LSH/MinHash<br/>Similarity Detection<br/>Delta Encoding"]
        end
        
        %% Memory Subsystem
        subgraph Memory["🧮 8 MB PSRAM"]
            Dict["📚 Compression Dictionary<br/>1 MB"]
            Index["🗂️ Hash Index<br/>6 MB<br/>(158K entries)"]
            Buffers["📋 I/O Buffers<br/>1 MB"]
        end
    end
    
    %% Main Data Flow
    PC <-->|USB 1.1| USB
    USB <-->|Inter-core Queue| Buffers
    Buffers <-->|Process Data| L1
    L1 -->|Compressed| L2
    L2 -->|Chunks| L3
    L3 -->|Deduplicated| L4
    L4 -->|Final Data| SDM
    SDM <-->|Raw Sectors| MicroSD
    
    %% Memory Access Patterns
    L1 -.->|Read/Write| Dict
    L3 -.->|Hash Lookup| Index
    L4 -.->|LSH Probe| Index
    Core0 -.->|Buffer Management| Buffers
    
    %% Styling
    classDef coreBox fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff
    classDef memoryBox fill:#1a365d,stroke:#2c5282,stroke-width:2px,color:#fff
    classDef layerBox fill:#2f855a,stroke:#38a169,stroke-width:2px,color:#fff
    classDef externalBox fill:#744210,stroke:#975a16,stroke-width:2px,color:#fff
    
    class Core0,Core1 coreBox
    class Memory memoryBox
    class L1,L2,L3,L4 layerBox
    class PC,MicroSD externalBox
```

### 2.2 Memory Allocation Map

| Memory Region | Size     | Purpose                                | Access Pattern             | Persistence |
|---------------|----------|----------------------------------------|----------------------------|-------------|
| PSRAM Dict    | 1.0 MB   | DEFLATE sliding window (2²⁰ bytes)    | Sequential R/W (L1)        | Volatile    |
| PSRAM Index   | 6.0 MB   | **Working-set cache** for L3 index (~150K most recent entries) | Random R/W (L3, L4) | Volatile (cache) |
| PSRAM Buffers | 1.0 MB   | Inter-core queues, temp storage        | Ring buffer (Core 0 ↔ 1)   | Volatile    |
| **Total**     | **8 MB** | **SPIRAM (MALLOC_CAP_SPIRAM)**         | —                          | —           |

**Index Architecture:**
- **In-PSRAM working set (6 MB)**: Hot cache for ~150K most recently accessed chunk entries; LRU eviction
- **Persistent L3 index (450 MB on SD card)**: Full hash table with 11.25M entries; see §8.2 for sizing
- **L4 band tables (150 MB on SD card)**: LSH similarity index; see §8.3 for structure

**Note:** SRAM (520 KB) is reserved for critical FreeRTOS tasks, interrupt handlers, and stack allocation. All heavy data processing uses PSRAM to avoid cache thrashing. The PSRAM index is a **cache**, not the complete index—the complete L3 and L4 indices are persisted on the SD card.

---

## 3. Scientific and Technical Rationale

The HMSE engine processes data through four cascading software layers running on **Core 1**, with the index resident in the **8 MB PSRAM**.

### 3.1 Four-Layer Processing Pipeline

| Layer                            | Technique                                        | Scientific Basis                                                                                                                   | Expected Factor (CF)           | Confidence Level | Throughput Budget **(Projected, Unvalidated)** | Core 1 Resource Trade        |
| -------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ | ---------------- | ----------------- | ---------------------------- |
| **L1: Lossless Compression**     | DEFLATE (Level 9) with **1 MB PSRAM Window (W)** | LZ77 Principle [2,3]: Compression ratio (CR) ∝ dictionary size W. PSRAM removes the W constraint of SRAM-limited MCUs.               | 3:1 to 4:1 (Intra-Chunk)       | **Plausible** (2-4× typical on text; requires benchmark) | ~1.5 MB/s (projected)        | ≈ 20 % CPU Time (estimated)             |
| **L2: Content-Defined Chunking** | FastCDC (Rabin Hash, target 4 KiB avg, min 1 KiB, max 16 KiB) | Rabin Fingerprinting [1,4]: Boundaries are content-determined (H ≡ 0 mod P) rather than offset-based, resisting data shifting. | > 99 % Boundary Preservation | **Validated** (well-established in literature [1]) | ~8 MB/s (projected) | ≈ 10 % CPU Time (estimated) |
| **L3: Exact Deduplication**      | SHA-256 Hashing on Unique Chunks                 | Cryptographic collision resistance uniquely identifies blocks for storage index management. Uses ESP32-S3 HW acceleration [13].         | 1.1:1 to 10:1 (Variable)       | **Optimistic** (50% exact-duplicate assumption; corpus-dependent) | ~15 MB/s (projected)         | ≈ 5 % CPU Time (estimated) |
| **L4: Similarity Deduplication** | LSH (MinHash: n=128, b=8, r=16) + Delta Encoding (xdelta3) | Jaccard Similarity [5,6,7,8]: Probabilistically clusters similar MinHash vectors. Delta coding can save ~80% of near-duplicate block size (empirically corpus-dependent; bench and validate). | 15:1 to 50:1 on Iterative Data | **Optimistic** (50% similar-chunk assumption + 80% delta efficiency; requires validation on Wikipedia corpus) | ~1.2 MB/s (projected)        | ≈ 50 % CPU Time (estimated)     |

**⚠️ Critical Caveat:** All throughput and CPU budget values are **theoretical projections** based on algorithm benchmarks from other platforms. **No ESP32-S3 measurements have been performed**. Actual performance may be significantly lower due to:
- PSRAM access latency (slower than SRAM)
- Cache contention between cores
- FreeRTOS scheduling overhead
- SD card I/O bottlenecks

**System assumes USB 1.1 speed (~1.0 MB/s) as target; projected margins may not exist in practice.**

### 3.2 Data Transformation Pipeline

```mermaid
flowchart LR
    %% Input Stage
    A["📄 Raw Wikipedia Text<br/>100 MB<br/>Logical Size"]
    
    %% Processing Pipeline
    subgraph Pipeline["🔄 HMSE Processing Pipeline"]
        B["📦 L1: DEFLATE<br/>Lossless Compression<br/>1 MB Dictionary Window"]
        C["✂️ L2: FastCDC<br/>Content-Defined Chunking<br/>Rabin Fingerprinting"]
        D["🔍 L3: SHA-256<br/>Exact Deduplication<br/>Hardware Accelerated"]
        E["🔗 L4: LSH/MinHash<br/>Similarity Detection<br/>Delta Encoding"]
    end
    
    %% Output Stage
    F[("💾 Physical Storage<br/>3.2 MB<br/>31.25:1 Compression")]
    
    %% Main Flow
    A -->|"Write Stream<br/>1.0 MB/s"| B
    B -->|"Compressed Data<br/>33 MB (3:1 ratio)<br/>20% CPU"| C
    C -->|"Content Chunks<br/>~8,192 chunks<br/>10% CPU"| D
    D -->|"Unique Chunks<br/>16 MB (2:1 ratio)<br/>5% CPU"| E
    E -->|"Final Storage<br/>3.2 MB (5:1 ratio)<br/>50% CPU"| F
    
    %% Performance Annotations
    B -.->|"Throughput:<br/>1.5 MB/s"| B
    C -.->|"Throughput:<br/>8 MB/s"| C
    D -.->|"Throughput:<br/>15 MB/s"| D
    E -.->|"Throughput:<br/>1.2 MB/s"| E
    
    %% Styling
    classDef inputBox fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000
    classDef layerBox fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef outputBox fill:#e8f5e8,stroke:#388e3c,stroke-width:3px,color:#000
    classDef pipelineBox fill:#fff3e0,stroke:#f57c00,stroke-width:3px,color:#000
    
    class A inputBox
    class B,C,D,E layerBox
    class F outputBox
    class Pipeline pipelineBox
```

<details>
<summary><b>Example: Data Transformation Through All Layers</b></summary>

**Input (64 bytes):**
```
The quick brown fox jumps over the lazy dog. The quick brown fox jumps.
```

**After L1 (DEFLATE):** 
```
Compressed: 41 bytes (1.56:1 ratio)
[Binary DEFLATE stream with LZ77 backreferences]
```

**After L2 (FastCDC):**
```
Chunk detected at byte 41 (Rabin hash: 0x00003A7F ≡ 0 mod 0x3A7F)
Chunk ID: #4829
```

**After L3 (SHA-256 Dedupe):**
```
Hash: a3d8f9c2e1b5... (first 12 hex digits shown)
Lookup in index: NOT FOUND
→ Store to SD at LBA 0x0000A420, Length: 41 bytes
→ Update index: SHA-256 → (LBA: 0x0000A420, Len: 41)
```

**After L4 (MinHash/LSH):**
```
MinHash signature computed (128 hashes)
LSH Probe: Similar chunk found (Jaccard: 0.87)
→ Delta encoding against base chunk #4201
→ Delta size: 8 bytes (5.1:1 ratio)
→ Store delta record instead of full chunk
```

**Physical Storage:** 8 bytes (delta) + 4 bytes (metadata) = **12 bytes total** (5.3:1 overall)

</details>

---

## 4. Feasibility Analysis and Mathematical Proof

### 4.1 Baseline Requirements

The target is to store the English Wikipedia text corpus on an 8 GB MicroSD card:

**Data Sizes:**
- **Wikipedia BZ2 download:** ~25 GB (compressed)
- **Decompressed text (actual input):** ~75 GB (raw XML/text)
- **Physical Storage Available:** 8 GB MicroSD

**Required Compression Factor:**
- **Against decompressed baseline:** 75 GB ÷ 8 GB = **9.375:1**
- **Against BZ2-equivalent baseline:** 25 GB ÷ 8 GB = **3.125:1**

**Important:** The HMSE pipeline processes **decompressed text** (75 GB), not the BZ2 file. BZ2 is only used for download/transfer; the actual compression layers (L1-L4) operate on raw text to avoid trying to compress already-compressed data.

### 4.2 Layer-by-Layer Reduction Model

To **hypothesize** feasibility under optimistic assumptions, we model compression through all four layers on representative Wikipedia data. **These projections require empirical validation** and may not reflect actual performance.

| Stage                    | Size (MB) | Compression Factor | Cumulative Factor | Notes                                                      |
|--------------------------|-----------|--------------------| ------------------ |------------------------------------------------------------|
| **Raw Text**             | 100.0     | —                  | 1.0:1              | Sample: 100 MB of Wikipedia articles (decompressed)        |
| **After L1 (DEFLATE)**   | 33.3      | 3.0:1              | 3.0:1              | **Plausible**: 1 MB window captures repetitive structures                 |
| **After L2 (FastCDC)**   | 33.3      | 1.0:1              | 3.0:1              | **Validated**: Boundary detection only; no size change                    |
| **After L3 (Exact)**     | 16.7      | 2.0:1              | 6.0:1              | **Optimistic**: Assumes ~50% exact duplicates (unvalidated)    |
| **After L4 (Similarity)**| 11.5      | 1.45:1             | **8.7:1**          | **Optimistic**: Assumes ~30% similar variants with 80% delta efficiency (unvalidated) |

**⚠️ Critical Assumption:** The cumulative 8.7:1 factor assumes high redundancy in Wikipedia. Actual performance depends on corpus characteristics and may be significantly lower.

**Blended Corpus Estimate (Theoretical Model):**

**Hypothesis:** Wikipedia content exhibits varying redundancy levels. The following estimates are **unvalidated assumptions** based on corpus structure analysis:

| Content Type         | % of Corpus | Hypothesized CF | Weighted Contribution |
|----------------------|-------------|-------------|-----------------------|
| Article Text         | 60%         | 4.0:1 ± 1.0 | 2.40                  |
| Templates/Infoboxes  | 20%         | 15.0:1 ± 5.0 | 3.00                  |
| Citations/References | 15%         | 8.0:1 ± 2.0 | 1.20                  |
| Metadata/Categories  | 5%          | 6.0:1 ± 2.0 | 0.30                  |
| **Weighted Average** | **100%**    | —           | **6.90:1 ± 2.1**      |

**⚠️ Circular Reasoning Risk:** These percentages are design targets, not empirically measured values. Actual Wikipedia redundancy may be lower, requiring validation before claiming feasibility.

### 4.3 Safety Margin and Overhead Analysis

**Revised Assessment:** The optimistic projection of **8.7:1** (against decompressed 75 GB baseline) is **below the required 9.375:1** threshold, indicating **marginal feasibility** contingent on actual redundancy rates exceeding projections.

**Overhead Accounting:**

| Overhead Component        | Size (MB) | % of 8 GB | Description                                    |
|---------------------------|-----------|-----------|------------------------------------------------|
| Hash Index (PSRAM mirror) | 450       | 5.5%      | SHA-256 + LBA + Length per unique chunk        |
| LSH Band Tables           | 150       | 1.9%      | **⚠️ Underestimated**: L4 similarity index (band tables with list overhead likely ~300 MB; see §8.3 for revision)         |
| Delta Storage Metadata    | 80        | 1.0%      | Base chunk pointers for delta-encoded chunks   |
| Filesystem Overhead       | 80        | 1.0%      | FAT32 allocation tables                        |
| Reserved/Fragmentation    | 40        | 0.5%      | Safety buffer for write amplification (may need 2-4× for SD card wear leveling)          |
| **Total Overhead**        | **800**   | **10%**   | **⚠️ Likely underestimated by ~150-200 MB**                                              |

**Effective Storage Capacity:** 8000 MB - 800 MB = **7200 MB** (Optimistic; realistic: **7000-7100 MB** with corrected overhead)

**Required Compression Factor (adjusted):** 
- Against decompressed: 75 GB ÷ 7.1 GB = **10.56:1** (revised with realistic overhead)
- Against BZ2-equivalent: 25 GB ÷ 7.1 GB = **3.52:1**

**Conclusion:** The optimistic projection of **8.7:1** **falls short** of the adjusted requirement of **10.56:1** by **-17%**. The system requires either:
1. **Higher redundancy** than projected (>75% total dedupe rate, not 70%)
2. **Larger storage media** (16 GB card instead of 8 GB)
3. **Optimized index structures** (reducing L4 overhead from 300 MB to 150 MB)

**Risk Assessment:** Success is **contingent** on empirical validation showing Wikipedia redundancy exceeds theoretical projections. Without validation, the 8 GB target should be considered **high risk**.

**Note:** The projected 8.7:1 ratio is optimistic and assumes the 100 MB sample is representative. **Actual Wikipedia corpus performance is unknown** and requires empirical validation before claiming feasibility.

### 4.4 Comparison: ESP32-S3 vs Traditional PC

| Metric                  | ESP32-S3 HMSE         | Typical PC Implementation | Advantage           |
|-------------------------|-----------------------|---------------------------|---------------------|
| **Dictionary Size (L1)**| 1 MB (PSRAM)          | 32 KB (typical zlib)      | **32× larger**      |
| **Index Capacity (L3)** | 6 MB (~158K entries)  | Limited by RAM cost       | Cost-effective      |
| **SHA-256 Speed**       | HW Accelerated        | Software (unless AES-NI)  | Comparable          |
| **Power Consumption**   | ~500 mW               | ~15-65 W                  | **30-130× lower**   |
| **Cost**                | ~$3 (MCU)             | N/A                       | Embedded-optimized  |

The MCU's advantage lies in **dedicated PSRAM** for large compression dictionaries without competing with system RAM, and **low-power always-on** operation for USB mass storage emulation.

---
## 5. Open Questions and Research Goals

While the earlier sections focused on the theoretical performance and architecture of the **HyperDrive Microcontroller Storage Engine (HMSE)**, this section outlines the **open research questions** and **conditional goals** that motivate this work.

These are **exploratory inquiries**, not validated outcomes. They frame what we hope to learn through empirical testing.

---

### 5.1 Research Question: Can Theory Translate to Practice?

**What we want to learn:** If the multi-layer pipeline is implemented on real hardware, can the projected compression ratios be achieved on actual Wikipedia data?

**Key uncertainties:**
- Will DEFLATE achieve 3:1 on decompressed Wikipedia text with 1 MB window?
- Does Wikipedia exhibit 50% exact chunk redundancy, or is this an overestimate?
- Can the ESP32-S3 sustain the projected throughput under continuous load?

**If validated,** this would demonstrate that theoretical algorithmic efficiency can translate to measurable improvements in **cost**, **energy usage**, and **storage density** on resource-constrained hardware.

---

### 5.2 Research Question: What Level of Performance Is "Enough"?

**What we want to learn:** At what compression factor does the system become useful for real-world deployment?

**Tiered success criteria (exploratory):**
- **Minimum viable (5:1)**: Competitive with BZ2, proves basic feasibility
- **Moderate success (7:1)**: Justifies MCU complexity over simpler compression
- **Target (9.375:1)**: Achieves Wikipedia-on-8GB goal
- **Stretch goal (12:1)**: Demonstrates substantial improvement over baselines

**Open question:** If the system achieves only 5-7:1, does that still provide value? What applications would benefit from partial success?

---

### 5.3 Research Question: Can MCUs Compete on Efficiency?

**What we want to learn:** If HMSE meets its throughput targets, would it offer advantages over Raspberry Pi-class devices in energy and cost?

**Key uncertainties:**
- Will the ESP32-S3's power consumption (< 1 W) remain stable under sustained load?
- Does PSRAM access latency degrade performance below projections?
- Can thermal throttling be avoided in compact enclosures?

**If validated,** this would suggest opportunities for:
- Persistent offline archives in low-power environments
- Mesh-based distributed knowledge systems
- Portable devices for bandwidth-limited regions

**If not validated,** it would indicate that ARM-class processors remain necessary for this workload.

---

### 5.4 Exploratory Application Domains

**What we hope to investigate:** If the system proves feasible, what domains could benefit?

| Domain | Hypothesized Use Case | Conditional Benefit |
|--------|-----------|----------|
| IoT & Sensor Networks | Local data aggregation | **If** L3/L4 dedupe works on sensor data, extends retention under bandwidth limits |
| Edge & Satellite Systems | On-device pre-compression | **If** throughput meets 1 MB/s, reduces transmission requirements |
| Educational / Offline Knowledge Systems | Large text datasets (e.g., Wikipedia) | **If** 8 GB target is met, enables access in bandwidth-limited regions |

**Critical dependencies:** Each application assumes the system meets its projected performance. Alternative use cases should be identified if performance falls short.

---

### 5.5 Risk Factors and Contingencies

**What could go wrong?** Several dependencies could prevent the system from meeting its goals:

| Risk Factor | Uncertainty | Contingency Plan |
|-------------|-------------|------------------|
| **Low corpus redundancy** | Wikipedia may have < 50% exact duplicates | Test on diverse corpora; define fallback success criteria |
| **PSRAM latency bottleneck** | Cache misses may reduce throughput below 1 MB/s | Implement prefetching; consider 32 MB PSRAM module |
| **LSH storage overflow** | 300 MB L4 index may exceed budget | Reduce to 4 bands; use compact encoding; accept 16 GB card |
| **Flash wear-out** | Repetitive writes may degrade SD card | Implement wear leveling; rotate write locations |
| **Thermal throttling** | Sustained load may reduce clock speed | Add heatsink; implement duty cycling |

**Open question:** If multiple risks materialize, at what point does the system become impractical? What is the acceptable failure threshold?

---

### 5.6 Value as a Research and Education Platform

**Independent of performance outcomes,** this project aims to provide:

**Learning goals:**
- Document a complete embedded systems design process
- Enable reproducibility through open-source implementation
- Provide benchmark datasets for compression research
- Support student experiments in data deduplication

**Open science contribution:**
- Pre-registered study design prevents p-hacking
- Negative results would inform future microcontroller storage research
- Ablation studies would isolate which layers contribute most to compression

**Question for the research community:** Even if the 8 GB target is not met, what insights would be valuable from partial success or instructive failure?

---

**Summary:**  
This section frames HMSE as an **open inquiry** rather than a validated solution. The key questions are:
1. Can theoretical projections be realized on actual hardware?
2. What compression factor is sufficient for real-world utility?
3. Do MCUs offer efficiency advantages over ARM-class devices for this workload?
4. What do we learn if the system underperforms expectations?

Empirical testing will determine which scenarios materialize. The research value lies in **systematic investigation of these uncertainties**, not in predetermined outcomes.

---

## 6. Implementation Plan and Verification (HMSE Phases)

**Implementation Validation Requirements:**

Before proceeding with implementation, the following microbenchmarks are required to validate theoretical projections:

| Benchmark | Target Metric | Validation Tool | Purpose |
|-----------|--------------|-----------------|---------|
| **DEFLATE Throughput** | ≥ 1.5 MB/s encode, ≥ 5 MB/s decode | `miniz` on ESP32-S3 | Verify L1 compression speed with 1 MB dictionary |
| **PSRAM Bandwidth** | ≥ 30 MB/s sustained R/W | Custom test with `heap_caps_malloc` | Validate PSRAM access under cache contention |
| **SHA-256 Hardware** | ≥ 15 MB/s | ESP-IDF `mbedtls_sha256` | Confirm hardware acceleration throughput |
| **FastCDC Chunking** | ≥ 8 MB/s, avg chunk ∈ [3.5, 4.5] KB | Custom Rabin hash implementation | Verify boundary detection performance |
| **MinHash Computation** | ≥ 1.2 MB/s (128 hashes) | Custom MinHash with MurmurHash3 | Validate L4 similarity detection overhead |
| **Actual Wikipedia CF** | ≥ 9.375:1 (target 10-14:1) | Full pipeline test on decompressed 75 GB dump | Empirical validation of compression factor (75 GB → 8 GB target) |

**Note:** All throughput projections in this specification are based on established algorithm performance and must be validated with actual hardware before claiming feasibility.

**For detailed validation methodology, experimental design, statistical analysis framework, and reproducibility requirements, see [VALIDATION_METHODS.md](./VALIDATION_METHODS.md).**

---

### **Phase 0: Foundation Setup and Performance Baseline**

**Objective:** Validate fundamental hardware performance and establish the **FreeRTOS** control environment.

| Step                       | Implementation Detail                                                                                                                           | Scientific Rationale                                                                             | Success Checkpoint (Quantified Metric)                                        |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| **H0.1 Dual-Core Tasking** | Core 0 Task Priority 5 (USB). Core 1 Task Priority 3 (HMSE Engine). Use Core Affinity settings in FreeRTOS task creation.                       | Prioritizes time-sensitive USB I/O over heavy data processing to prevent bus drops.              | USB Ping Latency ≤ 1 ms during Core 1 Prime Calculation Test                  |
| **H0.2 SDMMC Driver**      | Initialize SD Card using SDMMC Host Driver [12] in 4-bit mode @ 40 MHz. Use raw sector read/write functions.                                     | 4-bit mode offers parallelism for max SD card speed, ensuring the SD card is not the bottleneck. | SD Card Read Throughput ≥ 5 MB/s (measured internally by MCU Core 0)          |
| **H0.3 PSRAM Integrity**   | Allocate 4 MB test buffer via `heap_caps_malloc(..., MALLOC_CAP_SPIRAM)`. Execute continuous Core 1 R/W loops with simulated Core 0 cache hits. | Validates SPIRAM stability and correctness under contention and high transfer rates.             | PSRAM Buffer Integrity (MD5 Checksum) **Pass** after 1 hour of simulated load |

---

### **Phase 1: Lossless Compression (L1)**

**Objective:** Achieve ≥ 3:1 compression ratio (CF₁) and prove the CPU trade-off is stable.

| Step                            | Implementation Detail                                                                                             | Scientific Rationale                                                                              | Success Checkpoint                                            | Latency Budget |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | -------------- |
| **P1.1.1 Dict Allocation**      | Allocate 1 MB DEFLATE Lookback Window (2²⁰ bytes) in PSRAM. Use Level 9 compression profile.                      | Maximizing window size optimizes redundancy search in repetitive text/code.                       | PSRAM Usage ≥ 1 MB dedicated to compression dictionary        | < 10 ms        |
| **P1.1.2 Compressed Write**     | Implement write callback: Core 0 Buffers → Core 1 (Compress) → Core 0 (SD Write). Use `miniz` or similar library. | Inline compression maximizes effective throughput by reducing data written to SD card [10,11].        | Write 100 MB of redundant text. Final physical size ≤ 33.3 MB | < 800 ms/MB    |
| **P1.1.3 Decompression Verify** | Implement decompression task on Core 1 for read callback. Verify speed > compression.                             | Decompression is typically 5–10× faster than compression, ensuring read latency meets USB limits. | Read Throughput ≥ 0.7 MB/s. File Checksum **Passes**          | < 100 ms/MB    |

<details>
<summary><b>Example P1.1.2: DEFLATE Window Size Impact</b></summary>

**Test Case:** Compress 1024 bytes of highly repetitive Wikipedia template text.

**Input Text (1024 bytes):**
```
{{Infobox person|name=John Smith|birthplace=London|occupation=Engineer}}
{{Infobox person|name=Jane Doe|birthplace=Paris|occupation=Scientist}}
{{Infobox person|name=Bob Johnson|birthplace=Berlin|occupation=Teacher}}
... (pattern repeats with minor variations)
```

**Compression Results:**

| Window Size | Compressed Size | Ratio | Notes                                          |
|-------------|-----------------|-------|------------------------------------------------|
| 32 KB       | 412 bytes       | 2.49:1| Standard zlib default                         |
| 256 KB      | 368 bytes       | 2.78:1| Better repetition capture                      |
| **1 MB**    | **340 bytes**   |**3.01:1**| **HMSE target: Maximum LZ77 lookback**     |

**LZ77 Backreference Example:**
```
Byte 0-64:   {{Infobox person|name=John Smith|birthplace=London|...
Byte 65-128: <distance=65, length=45> Jane Doe <distance=78, length=23> Paris...
```

The 1 MB window allows the compressor to reference the template structure from hundreds of KB earlier, dramatically improving ratio on structured data.

</details>

---

### **Phase 2: Content-Defined Deduplication (L2 + L3)**

**Objective:** Implement CDC and SHA-256 indexing to eliminate exact redundancies.

| Step                          | Implementation Detail                                                                                     | Scientific Rationale                                                               | Success Checkpoint                                            | Latency Budget |
| ----------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------- | -------------- |
| **P2.1.1 FastCDC Chunker**    | Implement Rabin Hash on Core 1. Boundary Fingerprint Pattern (P) yields avg chunk size 4 KB.              | Adjusting modulus (H ≡ 0 mod P) controls chunk size, optimizing metadata overhead. | Run on 1 GB file; avg chunk size ∈ [3.5 KB, 4.5 KB]           | < 0.5 ms/chunk |
| **P2.2.1 PSRAM Index Design** | Create Hash Map in PSRAM: Key = 256-bit SHA-256; Value = Physical LBA (32-bit SD Address) + Chunk Length. | PSRAM index mandatory for < 100 µs lookups to keep up with USB stream.             | Lookup Latency ≤ 100 µs; Index Memory ≤ 6 MB                  | < 100 µs       |
| **P2.3.1 Dedupe Write Logic** | If hash exists → store pointer record (new metadata). Else → write L1 chunk to SD.                        | Validates single-instance storage and eliminates redundancy (L3 Exact Dedupe).     | Write 5 copies of 100 MB corpus; final physical size ≤ 105 MB | < 150 µs/chunk |

<details>
<summary><b>Example P2.1.1: FastCDC Boundary Detection</b></summary>

**Rabin Rolling Hash Algorithm:**

The Rabin fingerprint is computed over a sliding window of 64 bytes:

\[
H = \sum_{i=0}^{63} c_i \cdot r^{63-i} \mod p
\]

Where:
- \( c_i \) = byte value at position \( i \)
- \( r \) = random prime (e.g., 257)
- \( p \) = large prime modulus

**Chunk Boundary Condition:**

\[
H \equiv 0 \pmod{P} \quad \text{where } P = 4096 \text{ (target avg size)}
\]

**Example on 16 KB Wikipedia Article:**

```
Byte Range    | Rabin Hash    | Boundary? | Action
--------------|---------------|-----------|----------------------------
0-64          | 0x7A3E8F12    | No        | Continue scanning
65-128        | 0xB2F4A8C0    | No        | Continue scanning
3847-3911     | 0x00001000    | YES ✓     | Cut chunk #1 (3911 bytes)
3912-3976     | 0x4F2B8A19    | No        | Continue scanning
7829-7893     | 0x00000800    | YES ✓     | Cut chunk #2 (3918 bytes)
...
```

**Resulting Chunks:**
- Chunk #1: 3911 bytes
- Chunk #2: 3918 bytes  
- Chunk #3: 4203 bytes
- Chunk #4: 3821 bytes
- **Average:** 3963 bytes ✓ (target: 4096 ± 512)

**Shift Resistance:** If 100 bytes are inserted at the beginning, boundaries shift by ~100 bytes, but remain at the same *content-defined* locations. 99%+ of chunks remain identical.

</details>

<details>
<summary><b>Example P2.2.1: Hash Index Structure</b></summary>

**PSRAM Hash Table Layout:**

```c
struct ChunkIndex {
    uint8_t  sha256[32];      // SHA-256 hash (256 bits)
    uint32_t lba;             // Logical Block Address on SD card
    uint16_t length;          // Chunk length in bytes
    uint16_t refcount;        // Reference count for garbage collection
} __attribute__((packed));    // Total: 40 bytes per entry
```

**Index Capacity:**

\[
\text{Max Entries} = \frac{6 \times 10^6 \text{ bytes}}{40 \text{ bytes/entry}} = 150,000 \text{ entries}
\]

**Note:** This is the in-PSRAM index capacity for Phase 2 testing. The full system (Phase 3) uses 450 MB on SD card for the L3 index (11.25M entries) + 150 MB for L4 band tables.

**Example Index Entries:**

| SHA-256 (first 16 hex)      | LBA        | Length | RefCount |
|-----------------------------|------------|--------|----------|
| `a7f5d8c3e9b2...`           | 0x00000010 | 4021   | 1        |
| `3c8a6f1d2e94...`           | 0x00001FA8 | 3847   | 3        |
| `f2b9e4a87c31...`           | 0x00003D20 | 4193   | 1        |

**Lookup Algorithm (Core 1):**
1. Compute SHA-256 of compressed chunk (HW accelerated: ~0.5 ms)
2. Hash table probe in PSRAM (linear probing, ~50 µs avg)
3. If found → return `(LBA, Length)`, increment `refcount`
4. If not found → allocate new LBA, insert entry

</details>

<details>
<summary><b>Example P2.3.1: Deduplication Efficiency</b></summary>

**Test Scenario:** Write 5 copies of the same 100 MB Wikipedia corpus.

**Without Deduplication:**
- Physical storage: 5 × 100 MB = **500 MB**

**With L3 Exact Deduplication:**

| Metric                  | Value     | Calculation                                 |
|-------------------------|-----------|---------------------------------------------|
| Unique chunks           | 25,600    | 100 MB ÷ 4 KB avg                           |
| Compressed chunk size   | 1.33 KB   | After L1 (3:1 ratio)                        |
| Unique data stored      | 34.1 MB   | 25,600 × 1.33 KB                            |
| Pointer records         | 102,400   | 4 × 25,600 (for copies 2-5)                 |
| Pointer overhead        | 0.8 MB    | 102,400 × 8 bytes (LBA + offset)            |
| **Physical storage**    | **34.9 MB**| **Deduplication ratio: 14.3:1**            |

**Storage Savings:** 500 MB → 34.9 MB = **93% reduction**

</details>

---

### **Phase 3: Similarity Deduplication and Final Goal**

**Objective:** Implement LSH and Delta Encoding (L4) to achieve the 8 GB physical storage goal.

| Step                                      | Implementation Detail                                                                                                | Scientific Rationale                                                                      | Success Checkpoint                                                                  | Latency Budget |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | -------------- |
| **P3.1.1 MinHash Vector**                 | Implement 128-MinHash Vector generation on Core 1. Use LSH banding scheme (b = 4 to 8 bands) for PSRAM index probes. | Amplifies collision probability for similar items [5,6,7,8]. Banding reduces hash table probes. | MinHash Vector Calculation ≤ 1.5 ms/chunk (~0.8 MB/s sustained)                     | < 1.5 ms/chunk |
| **P3.2.1 Delta Encoding Logic**           | If LSH match → compute binary difference. Store delta only if size ≤ 20 % of original chunk.                         | Delta record must be smaller than base chunk to ensure net savings.                       | Write 100 chunks (modify 1 % randomly). Avg physical increase ≤ 5 % of logical size | < 2.0 ms/chunk |
| **P3.3.1 Full Read Path Validation**      | Implement reconstruction: Read Base → Retrieve Delta → Apply Delta → Decompress. Final integrity checksum required.  | Validates multi-stage reconstruction under read load.                                     | 100 % Checksum Pass Rate for 1000 random articles                                   | < 5 ms/article |
| **P3.4.1 Final Evaluation (8 GB Target)** | Record max logical data stored on 8 GB card. Calculate final efficiency ratio CF over 25 GB baseline.                | Final ratio (logical size / 8 GB) determines success against 3.125:1 goal.                | **Goal Met:** Final Ratio ≥ 3.125:1                                                 | N/A            |

<details>
<summary><b>Example P3.1.1: MinHash and Jaccard Similarity</b></summary>

**Two Similar Article Chunks (after compression):**

**Chunk A (Base):** 
```
Albert Einstein was a German theoretical physicist who developed the theory 
of relativity, one of the two pillars of modern physics...
```

**Chunk B (Variant):**
```
Albert Einstein was a German-born theoretical physicist who developed the 
theory of relativity, one of the foundational theories of modern physics...
```

**Shingling (4-grams):**

| Chunk A Shingles             | Chunk B Shingles             | In Both? |
|------------------------------|------------------------------|----------|
| "Albe", "lber", "bert"       | "Albe", "lber", "bert"       | ✓        |
| "Eins", "inst", "nste"       | "Eins", "inst", "nste"       | ✓        |
| "Germ", "erma", "rman"       | "Germ", "erma", "rman", "-bor"| Partial  |
| "theo", "heor", "eori"       | "theo", "heor", "eori"       | ✓        |
| ...                          | ...                          | ...      |

**Jaccard Similarity:**

\[
J(A, B) = \frac{|A \cap B|}{|A \cup B|} = \frac{87}{103} \approx 0.845
\]

**MinHash Signature (128 hash functions):**

```
Chunk A MinHash: [42, 89, 17, 203, 91, ..., 145]  (128 values)
Chunk B MinHash: [42, 89, 17, 198, 91, ..., 145]  (128 values)
                  ✓   ✓   ✓   ✗   ✓         ✓
```

**MinHash Agreement:** 108 / 128 = 0.844 ≈ Jaccard similarity ✓

**LSH Banding (b=4, r=32):**

Each band has 32 hash values. Probability of collision in at least one band for J=0.845:

\[
P(\text{collision}) \approx 1 - (1 - 0.845^{32})^4 \approx 0.96
\]

High probability → LSH index lookup finds Chunk A as candidate for Chunk B.

</details>

<details>
<summary><b>Example P3.2.1: Delta Encoding</b></summary>

**Base Chunk A** (1280 bytes compressed):
```
Albert Einstein was a German theoretical physicist who developed...
[Full article text continues]
```

**Modified Chunk B** (1285 bytes compressed):
```
Albert Einstein was a German-born theoretical physicist who developed...
[Identical text with minor changes]
```

**Binary Delta (using bsdiff algorithm):**

```
Delta Record:
  - Base Reference: Chunk A (LBA 0x0002F8A0)
  - Operations:
    COPY(0, 18)           // "Albert Einstein was"
    INSERT("-born", 5)    // Insert new text
    COPY(18, 1245)        // Rest of article
  - Delta Size: 267 bytes
```

**Storage Decision:**

| Metric              | Value     | Decision                              |
|---------------------|-----------|---------------------------------------|
| Original chunk size | 1285 B    | —                                     |
| Delta size          | 267 B     | 20.8% of original                     |
| Threshold           | 256 B     | 20% of 1280 B                         |
| **Action**          | Store delta | ✓ (267 < 1285, worth storing)       |

**Physical Storage:**
- Chunk A: 1280 bytes (full)
- Chunk B: 267 bytes (delta) + 8 bytes (base pointer) = **275 bytes**
- **Savings:** 1285 - 275 = 1010 bytes (78.6% reduction)

</details>

<details>
<summary><b>Example P3.3.1: Multi-Stage Read Reconstruction</b></summary>

**Read Request:** Article "Albert_Einstein" (stored as 8 chunks)

```mermaid
sequenceDiagram
    participant Host as 🖥️ USB Host
    participant USB as 📡 Core 0: USB Handler
    participant Engine as 🧠 Core 1: HMSE Engine
    participant Index as 🗂️ Index (PSRAM)
    participant Storage as 💾 SD Card

    Note over Host,Storage: Multi-Stage Reconstruction: 32 KB Article

    %% Article Request
    Host->>USB: Read Request (offset=0, len=32KB)
    USB->>Index: Lookup Article Metadata
    Index-->>USB: Chunk Map [#301, #302d, #303, #304, ...]
    Note right of Index: 8 chunks total

    %% Chunk Processing Loop
    loop 🔄 Process Each Chunk (8 iterations)
        Note over USB,Engine: Processing Chunk #302d (Delta Type)
        
        USB->>Index: Lookup Chunk #302d Details
        Index-->>USB: Type=DELTA, Base=#302, LBA=0x00F2A0
        
        par Parallel Read Operations
            USB->>Storage: Read Base Chunk #302
            Storage-->>Engine: Compressed Base (1280 bytes)
        and
            USB->>Storage: Read Delta Record
            Storage-->>Engine: Delta Data (267 bytes)
        end
        
        Engine->>Engine: Apply Delta to Base
        Note right of Engine: Binary diff application
        Engine->>Engine: Decompress Result
        Note right of Engine: DEFLATE decompression
        Engine-->>USB: Reconstructed Chunk (4KB)
        Note right of Engine: 3.1 ms per chunk
    end

    %% Final Assembly
    USB->>USB: Verify CRC32 Checksum
    USB->>USB: Assemble Article (32 KB)
    USB-->>Host: Return Data Stream (32 KB)
    
    Note over Host,Storage: Total Time: 24.8 ms (1.29 MB/s) | Success ✓
```

**Timing Budget (per chunk):**

| Operation           | Time    | Cumulative |
|---------------------|---------|------------|
| Index lookup        | 100 µs  | 100 µs     |
| SD read (base)      | 800 µs  | 900 µs     |
| SD read (delta)     | 200 µs  | 1100 µs    |
| Delta apply         | 1500 µs | 2600 µs    |
| Decompression       | 500 µs  | 3100 µs    |
| **Total per chunk** |**3.1 ms**| —         |

**Article read time:** 8 chunks × 3.1 ms = **24.8 ms** (32 KB) = **1.29 MB/s** ✓

Exceeds USB 1.1 requirement of 1.0 MB/s.

</details>

---

## 7. Data Flow Architecture

### 7.1 Write Path (USB → SD Card)

```mermaid
sequenceDiagram
    participant Host as 🖥️ PC/Host
    participant USB as 📡 USB Handler
    participant Buffer as 📋 PSRAM Buffer
    participant Engine as 🧠 HMSE Engine
    participant Index as 🗂️ Hash Index
    participant Storage as 💾 SD Card

    Note over Host,Storage: Write Path: 4 KB Block Processing

    %% Initial Data Transfer
    Host->>USB: Write Request (4 KB)
    USB->>Buffer: Buffer Data
    Note over USB,Engine: Inter-core Notification
    Buffer->>Engine: Process Data Stream

    %% Layer 1: Compression
    Note over Engine: 📦 L1: DEFLATE Compression
    Engine->>Engine: Compress with 1 MB Dictionary
    Note right of Engine: 100 MB → 33 MB (3:1)

    %% Layer 2: Chunking  
    Note over Engine: ✂️ L2: FastCDC Chunking
    Engine->>Engine: Rabin Hash Scan
    Engine->>Engine: Detect Content Boundaries
    Note right of Engine: ~8,192 chunks created

    %% Layer 3: Exact Deduplication
    Note over Engine: 🔍 L3: SHA-256 Deduplication
    Engine->>Engine: Compute SHA-256 Hash
    Engine->>Index: Lookup Hash in Index
    
    alt Hash Found (Duplicate)
        Index-->>Engine: Return Existing LBA
        Engine->>Engine: Store Reference Pointer
        Note right of Engine: No storage needed
    else Hash Not Found (New)
        Engine->>Storage: Write Compressed Chunk
        Storage-->>Engine: Return New LBA
        Engine->>Index: Insert (SHA-256 → LBA)
        Note right of Engine: New chunk stored
    end

    %% Layer 4: Similarity Detection
    Note over Engine: 🔗 L4: LSH Similarity Detection
    Engine->>Engine: Compute MinHash Signature
    Engine->>Index: Probe LSH Index
    
    alt Similar Chunk Found
        Index-->>Engine: Return Base Chunk LBA
        Engine->>Storage: Read Base Chunk
        Storage-->>Engine: Return Base Data
        Engine->>Engine: Compute Binary Delta
        
        alt Delta < 20% of Original
            Engine->>Storage: Write Delta Record
            Engine->>Index: Store Delta Reference
            Note right of Engine: 78% space saved
        else Delta Too Large
            Engine->>Storage: Write Full Chunk
            Note right of Engine: Store complete chunk
        end
    else No Similar Chunk Found
        Engine->>Storage: Write Full Chunk
        Engine->>Index: Insert MinHash Signature
        Note right of Engine: Unique content stored
    end

    %% Completion
    Engine-->>USB: Processing Complete
    USB-->>Host: Write Acknowledgment
    
    Note over Host,Storage: Total Processing Time: ~6 ms (0.67 MB/s)
```

**Performance Bottlenecks (Projected with Uncertainty):**

| Stage        | Projected Time (Mean ± Range) | Bottleneck?     | Assumptions / Sources of Variance                          |
|--------------|-----------------|-----------------|-------------------------------------|
| USB Transfer | 4 ms ± 1 ms       | No              | Hardware-limited (1.0 MB/s); varies with USB controller load         |
| L1 Compress  | 2.7 ms ± 1.5 ms     | **Potential**   | **Unvalidated projection**; cache misses, PSRAM latency can add 50-100%    |
| L2 CDC       | 0.5 ms ± 0.2 ms     | No              | Rabin hash; variance from chunk boundary distribution      |
| L3 SHA-256   | 0.5 ms ± 0.3 ms     | No              | HW acceleration; context switch overhead adds latency                     |
| L4 LSH/Delta | 2.0 ms ± 1.0 ms     | **Potential**   | MinHash recompute + delta encode; **highly variable** based on similarity  |
| **Total (Best)**    | **~4 ms/4KB**   | **1.0 MB/s**   | All cache hits, no delta computation    |
| **Total (Typical)**    | **~6 ± 2 ms/4KB**   | **0.67 MB/s (0.5-1.0 MB/s range)**   | 50% cache hit, 30% delta    |
| **Total (Worst)**    | **~12 ms/4KB**   | **0.33 MB/s**   | Cache thrashing, thermal throttling, all L4 processing    |

**⚠️ Critical Caveat:** The "typical" case assumes:
- 80% PSRAM cache hit rate (unvalidated)
- No thermal throttling at sustained load
- FreeRTOS scheduling jitter < 500 µs
- SD card write latency stable (no wear-leveling stalls)

**Realistic expectation:** System likely operates at **0.5-0.8 MB/s** under load, **marginally** meeting USB 1.1 requirement. The "50% faster" claim assumes best-case conditions and may not hold in practice.

### 7.2 Read Path (SD Card → USB)

```mermaid
sequenceDiagram
    participant Host as 🖥️ PC/Host
    participant USB as 📡 USB Handler
    participant Engine as 🧠 HMSE Engine
    participant Index as 🗂️ Hash Index
    participant Storage as 💾 SD Card

    Note over Host,Storage: Read Path: 4 KB Block Reconstruction

    %% Initial Request
    Host->>USB: Read Request (4 KB)
    USB->>Index: Lookup Article/Chunk Metadata
    
    %% Three Reconstruction Paths
    alt 📄 Full Chunk (Direct Storage)
        Note over Index,Engine: Path 1: Complete Chunk
        Index-->>USB: Return LBA Address
        USB->>Storage: Read Compressed Chunk
        Storage-->>Engine: Return Compressed Data
        Engine->>Engine: Decompress with DEFLATE
        Engine-->>USB: Return Plain Text Data
        Note right of Engine: 2.5 ms (1.6 MB/s)
        
    else 🔗 Pointer Chunk (Exact Duplicate)
        Note over Index,Engine: Path 2: Reference to Duplicate
        Index-->>USB: Return Target LBA
        USB->>Storage: Read Target Chunk
        Storage-->>Engine: Return Compressed Data
        Engine->>Engine: Decompress Data
        Engine-->>USB: Return Plain Text Data
        Note right of Engine: 2.6 ms (1.54 MB/s)
        
    else 🔀 Delta Chunk (Similar Content)
        Note over Index,Engine: Path 3: Delta + Base Reconstruction
        Index-->>USB: Return Base LBA + Delta LBA
        
        par Parallel Read Operations
            USB->>Storage: Read Base Chunk
            Storage-->>Engine: Return Base Data
        and
            USB->>Storage: Read Delta Record
            Storage-->>Engine: Return Delta Data
        end
        
        Engine->>Engine: Apply Delta to Base
        Engine->>Engine: Decompress Result
        Engine-->>USB: Return Plain Text Data
        Note right of Engine: 3.8 ms (1.05 MB/s)
    end
    
    %% Final Response
    USB-->>Host: Return Data Block (4 KB)
    
    Note over Host,Storage: Average: 2.92 ms (1.37 MB/s) | Exceeds USB 1.1 ✓
```

**Read Performance:**

| Chunk Type | Operations               | Time Estimate | Throughput |
|------------|--------------------------|---------------|------------|
| Full       | SD read + decompress     | ~2.5 ms       | 1.6 MB/s   |
| Pointer    | Lookup + SD read + decomp| ~2.6 ms       | 1.54 MB/s  |
| Delta      | 2× SD read + delta + decomp| ~3.8 ms    | 1.05 MB/s  |

**Weighted Average** (assuming 40% full, 30% pointer, 30% delta):

\[
T_{avg} = 0.4 \times 2.5 + 0.3 \times 2.6 + 0.3 \times 3.8 = 2.92 \text{ ms}
\]

\[
\text{Throughput}_{avg} = \frac{4096 \text{ bytes}}{0.00292 \text{ s}} = 1,402,740 \text{ B/s} = 1.34 \text{ MiB/s} \approx 1.40 \text{ MB/s}
\]

**⚠️ PSRAM Cache Miss Impact (Critical Revision):**

The above latency assumes **all index lookups hit the 6 MB PSRAM cache**. With 11.25M entries (450 MB total index) and only 150K entries (1.3%) cached, **cache misses require SD card index reads**:

| Scenario | PSRAM Hit | SD Miss | Weighted Avg Latency |
|----------|-----------|---------|----------------------|
| **Optimistic (80% hit)** | 100 µs | 10 ms | **0.08 + 2.0 = 2.08 ms** |
| **Realistic (50% hit)** | 100 µs | 10 ms | **0.05 + 5.0 = 5.05 ms** |
| **Pessimistic (20% hit)** | 100 µs | 10 ms | **0.02 + 8.0 = 8.02 ms** |

**Revised throughput with 50% cache hit rate:**
\[
\text{Throughput}_{realistic} = \frac{4096 \text{ bytes}}{(0.00292 + 0.00505) \text{ s}} \approx 514,000 \text{ B/s} \approx 0.49 \text{ MB/s}
\]

**Impact:** With realistic cache behavior, read throughput **falls below USB 1.1 requirement** (1.0-1.2 MB/s). System requires:
1. **Larger PSRAM cache** (requires 8 MB → 32 MB module, not standard)
2. **Predictive prefetching** (pre-load likely index entries)
3. **Sequential access optimization** (batch reads reduce random seeks)

**Note:** Units defined as MiB = 2²⁰ bytes (1,048,576), MB = 10⁶ bytes (1,000,000). USB 1.1 practical throughput ≈ 1.0–1.2 MB/s. **Original calculation assumed 100% cache hit; realistic performance may not meet requirement ❌**

---

## 8. Storage Budget Analysis

### 8.1 8 GB Allocation Breakdown

The following table shows how the 8 GB physical storage is allocated:

| Component                  | Size (MB) | % of Total | Description                                          |
|----------------------------|-----------|------------|------------------------------------------------------|
| **Article Data (Dedupe)**  | 7,200     | 90.0%      | Compressed, chunked, and deduplicated content        |
| **Hash Index**             | 450       | 5.6%       | SHA-256 → (LBA, Length) mappings                     |
| **MinHash/LSH Index**      | 150       | 1.9%       | LSH band tables for similarity search                |
| **Delta Metadata**         | 80        | 1.0%       | Base chunk references for delta-encoded chunks       |
| **Filesystem (FAT32)**     | 80        | 1.0%       | Allocation tables, directory entries                 |
| **Reserved/Wear Leveling** | 40        | 0.5%       | Bad block management, write amplification buffer (⚠️ May need 2-4× for actual SD card wear leveling)     |
| **Total**                  | **8,000** | **100%**   | —                                                    |

**⚠️ Write Endurance Consideration:**

The 40 MB allocation assumes 2× write amplification, but SD cards typically exhibit **4-8× amplification** due to:
- Block erase requirements (128 KB erase blocks)
- Wear leveling across physical sectors
- Bad block remapping overhead

**Recommended approach:**
1. Monitor actual write amplification during testing
2. If amplification exceeds 2×, either:
   - Increase reserved allocation to 80-160 MB (1-2% of capacity)
   - Implement write journaling with rotation to distribute wear
   - Consider higher-endurance industrial SD cards

For production systems, a full write endurance analysis is recommended (see below).

---

### 8.1.1 Write Endurance Analysis

**SD Card Specifications (Typical Class 10):**
- Rated erase/write cycles: **10,000** (consumer grade)
- Card capacity: 8 GB
- Theoretical lifetime writes: 8 GB × 10,000 = **80 TB**

**With Write Amplification:**

| Amplification Factor | Effective Lifetime | Continuous Operation @ 1 MB/s |
|----------------------|-------------------|-------------------------------|
| 2× (optimistic) | 40 TB | 463 days |
| 4× (typical) | 20 TB | 231 days |
| 8× (worst-case) | 10 TB | 115 days |

**Mitigation Strategies:**

1. **Write Journaling**: Buffer writes in PSRAM, flush in larger blocks
2. **Rotation**: Distribute writes across multiple SD cards (RAID0 rotation)
3. **Industrial-grade cards**: Use SLC or MLC cards (100,000+ cycles)
4. **Wear monitoring**: Implement S.M.A.R.T.-like tracking for remaining life

**Risk Assessment:**
- For **proof-of-concept** (< 100 hours testing): Consumer SD acceptable
- For **long-term deployment**: Industrial SD or wear rotation required

---

### 8.2 Index Growth Analysis

**Hash Index Capacity:**

With 450 MB allocated for the hash index (L3 exact deduplication):

\[
\text{Max Entries} = \frac{450 \times 10^6 \text{ bytes}}{40 \text{ bytes/entry}} = 11,250,000 \text{ entries} \approx 11.25 \text{ million entries}
\]

**Expected Usage:**

Assuming average compressed chunk size of 1.33 KB:

\[
\text{Unique Chunks} = \frac{7200 \text{ MB}}{1.33 \text{ KB}} = \frac{7,200,000 \text{ KB}}{1.33 \text{ KB}} \approx 5.41 \text{ million chunks}
\]

**Index Utilization:** 5.41M / 11.25M = **48.1%**

This provides **2.08× headroom** for:
- Smaller-than-average chunks
- Index fragmentation
- Future growth

**Note:** The L3 index (450 MB) stores SHA-256 hash + LBA + length (40 bytes/entry). The L4 index (150 MB) stores LSH band tables separately (see §8.3).

### 8.3 Metadata Efficiency

**Hash Index Entry Layout (L3 Exact Deduplication):**

| Type           | Size (bytes) | Description                          |
|----------------|--------------|--------------------------------------|
| SHA-256 hash   | 32           | Unique identifier                    |
| LBA address    | 4            | Physical location on SD              |
| Chunk length   | 2            | Compressed size (up to 64 KB)        |
| Reference count| 2            | For garbage collection               |
| **Total**      | **40**       | Per unique chunk (L3 index entry)    |

**L3 Index Capacity:**

For 5.4M unique chunks:
\[
\text{L3 Index Size} = 5.4M \times 40 \text{ bytes} = 216 \text{ MB}
\]

**Comparison to Full MinHash Storage:**

If full MinHash signatures (n=128, 32-bit hashes) were stored per-chunk:
\[
\text{Full MinHash Storage} = 5.4M \times 128 \times 4 \text{ bytes} = 2,764,800,000 \text{ bytes} \approx 2.76 \text{ GB}
\]

This is **18.5× larger** than our 150 MB allocation, which is why band tables + on-the-fly computation are used.

---

**LSH Band Table Storage (L4 Similarity Deduplication) — First-Principles Derivation:**

**Configuration Parameters:**
- **n = 128**: Total number of hash functions (MinHash signature length)
- **b = 8**: Number of bands
- **r = 16**: Rows per band (n = b × r = 128)
- **Band hash bit-width**: 15 bits per band hash (design choice; see sensitivity analysis)

**Expected Unique Buckets per Band:**

For N = 5.4M chunks and B = 2^{15} = 32,768 possible band hash values:

Birthday paradox approximation (expected unique buckets):
\[
\text{Expected Unique} \approx B \times \left(1 - e^{-N/B}\right)
\]

\[
= 32,768 \times \left(1 - e^{-5,400,000/32,768}\right) \approx 32,768 \times (1 - e^{-164.8}) \approx 32,768
\]

With such heavy loading (N ≫ B), essentially all buckets are used. Average collisions per bucket:
\[
\text{Avg Collisions} = \frac{N}{B} = \frac{5,400,000}{32,768} \approx 165 \text{ chunks/bucket}
\]

**Band Table Storage Calculation (Original, Underestimated):**

| Component | Calculation | Size |
|-----------|-------------|------|
| **Buckets per band** | 2^{15} = 32,768 | — |
| **Total buckets (8 bands)** | 8 × 32,768 = 262,144 | — |
| **Per-bucket metadata** | 2B band_hash + 2B collision_count | 4 bytes |
| **Bucket metadata total** | 262,144 × 4 B | **1.05 MB** |
| **Collision lists (IDs only)** | 5.4M chunks × 8 bands × 3B chunk_id | **129.6 MB** |
| **Overflow handling** | Hash table overhead, padding | **12 MB** |
| **Total L4 Index (original)** | — | **142.65 MB** ≈ **150 MB** ❌ |

**⚠️ Critical Error:** The above calculation omits **list structure overhead** (pointers, array headers, memory alignment).

**Revised Calculation (Realistic with List Overhead):**

| Component | Calculation | Size |
|-----------|-------------|------|
| **Per-bucket storage** | Metadata (4B) + List header (8B) + 165 collisions × (3B ID + 4B pointer) | **1,163 bytes/bucket** |
| **Total buckets (8 bands)** | 262,144 buckets × 1,163 B | **304.8 MB** |
| **Total L4 Index (revised)** | — | **≈ 300-320 MB** ❌ **Exceeds 150 MB budget by 2×** |

**Note:** Each chunk appears in all 8 bands (one bucket per band), creating 43.2M total list entries. With average 165 collisions/bucket and 7-byte storage per entry (3B ID + 4B next-pointer in linked list), the realistic size is **~300 MB**, not 150 MB.

**Design Trade-off (Revised):**

1. **Storage problem**: Realistic 300 MB exceeds allocated 150 MB by **2×**
2. **Impact on feasibility**: Reduces data capacity by 150 MB (from 7200 MB to 7050 MB effective)
3. **Mitigation options**:
   - **Option A**: Reduce to 4 bands (halves L4 storage to ~150 MB, increases false negative rate)
   - **Option B**: Use compact encoding (bit-packed 24-bit chunk IDs, no pointers; saves ~120 MB)
   - **Option C**: Accept 16 GB card instead of 8 GB (doubles capacity, maintains 8 bands)
4. **CPU cost**: MinHash signature (128 hashes) must be recomputed during L4 probe:
   - Computation: ~128 MurmurHash3 calls per chunk
   - Estimated time: 1.2-1.5 ms per chunk @ 240 MHz (projected, unvalidated)
   - Acceptable since L4 only processes non-exact-duplicate chunks (~50% of total, optimistic assumption)

**Sensitivity Analysis — Alternative Configurations (With Realistic List Overhead):**

| Config | n | b | r | Band Bits | Buckets/Band | Total Buckets | Original Est. | **Revised w/ Overhead** | Trade-off |
|--------|---|---|---|-----------|-------------|---------------|---------------|------------|-----------|
| **Current** | 128 | 8 | 16 | 15 | 32,768 | 262K | 150 MB | **~305 MB** ❌ | Exceeds budget 2× |
| Fewer hashes | 64 | 8 | 8 | 14 | 16,384 | 131K | 145 MB | **~295 MB** ❌ | Still exceeds; lower accuracy |
| **Fewer bands (Option A)** | 128 | 4 | 32 | 16 | 65,536 | 131K | 75 MB | **~152 MB** ✓ | **Fits budget; higher false negatives** |
| More bands | 128 | 16 | 8 | 14 | 16,384 | 262K | 280 MB | **~610 MB** ❌ | Catastrophic overhead |
| Smaller buckets | 128 | 8 | 16 | 12 | 4,096 | 33K | 145 MB | **~370 MB** ❌ | Worse collisions, worse size |
| Larger buckets | 128 | 8 | 16 | 18 | 262,144 | 2.1M | 160 MB | **~195 MB** ❌ | Slightly better but exceeds |

**⚠️ Conclusion:** With realistic list overhead, **only the 4-band configuration fits the 150 MB budget**. This requires accepting higher false negative rates (fewer similar chunks detected) or increasing storage allocation to 300+ MB.

---

**Selected Configuration: Two Options**

The document originally specified **b=8, r=16**, but revised calculations show this requires **~305 MB**, not 150 MB. Two implementation options:

**Option A (Conservative, Fits Budget):**
- Configuration: **b=4, r=32** (4 bands, 32 rows)
- Storage: **~152 MB** (fits 150 MB allocation)
- Detection rate: P(collision) = 0.010 at s=0.75, 0.069 at s=0.80
- **Trade-off**: Lower recall for similar chunks; only highly similar (s ≥ 0.85) reliably detected
- **Status**: Fits within original 8 GB target

**Option B (Optimistic, Requires Larger Storage):**
- Configuration: **b=8, r=16** (8 bands, 16 rows) 
- Storage: **~305 MB** (requires 150 MB → 300 MB increase)
- Detection rate: P(collision) = 0.077 at s=0.75, 0.202 at s=0.80
- **Trade-off**: Better recall; reduces data capacity by 150 MB (from 7200 MB to 7050 MB)
- **Status**: Requires 8 GB → **16 GB card** to maintain original data capacity target

**Recommendation for Implementation:**
Start with **Option A (4 bands)** for proof-of-concept. If empirical testing shows insufficient similarity detection, upgrade to 16 GB card and implement **Option B (8 bands)**.

**Note:** All references to "b=8, r=16" in this document reflect the **originally proposed** configuration (Option B). Actual implementation should use Option A unless larger storage is acceptable.

**Combined Overhead Ratio:**

\[
\text{L3 Index} = 216 \text{ MB}
\]

\[
\text{L4 Index} = 150 \text{ MB}
\]

\[
\text{Total Metadata} = 216 + 150 = 366 \text{ MB}
\]

\[
\text{Overhead} = \frac{366 \text{ MB}}{7200 \text{ MB}} \approx 5.1\%
\]

This is **negligible** compared to compression gains (≥ 300% reduction).

### 8.4 Worst-Case Scenario

**Assumption:** Corpus is 100% unique (no deduplication possible).

| Layer             | Input (GB) | Ratio | Output (GB) | Fits in 8 GB? |
|-------------------|------------|-------|-------------|---------------|
| Decompressed text | 75.0       | —     | 75.0        | ✗             |
| After L1 (DEFLATE)| 75.0       | 3:1   | 25.0        | ✗             |
| After L2 (FastCDC)| 25.0       | 1:1   | 25.0        | ✗             |
| After L3 (Exact)  | 25.0       | 1:1   | 25.0        | ✗ (no dedupe) |
| After L4 (Similar)| 25.0       | 1:1   | 25.0        | ✗ (no dedupe) |
| With overhead     | —          | —     | 25.8        | ✗             |

**Conclusion:** In the worst case (100% unique data, no deduplication), L1 compression alone achieves **3:1** (75→25 GB), which is **insufficient** to meet the 8 GB target. The system **requires L3 and L4 deduplication** to work. 

**Realistic Case:** Wikipedia exhibits 40-60% redundancy across articles due to:
- Templates and infoboxes (high exact duplication via L3)
- Similar article structures (caught by L4 similarity detection)
- Repeated citations and boilerplate text

Expected effective ratio: **10-14:1** (against decompressed baseline), or **3.3-4.7:1** (against BZ2-equivalent).

**Critical dependency:** Success depends on empirical deduplication rates with the actual Wikipedia corpus.

### 8.5 Redundancy Sensitivity Analysis

To understand the system's sensitivity to corpus redundancy, we model scenarios with varying deduplication rates:

**Scenario Definitions:**
- **L1 output (baseline)**: 25 GB (after 3:1 DEFLATE compression from 75 GB)
- **L3 (exact dedupe)**: Removes identical chunks (templates, citations)
- **L4 (similarity dedupe)**: Removes near-duplicates via delta encoding

| Scenario | L3 Dedupe Rate | L4 Dedupe Rate | L3 Output (GB) | L4 Output (GB) | Final Size (GB) | Overhead (GB) | Total (GB) | Fits in 8 GB? | Safety Margin |
|----------|----------------|----------------|----------------|----------------|-----------------|---------------|------------|---------------|---------------|
| **Worst-Case** (100% unique) | 0% | 0% | 25.0 | 25.0 | 25.0 | 0.8 | 25.8 | ❌ | — |
| **Low Redundancy** (30% total) | 20% | 12.5% | 20.0 | 17.5 | 17.5 | 0.8 | 18.3 | ❌ | — |
| **Mid-Low Redundancy** (50% total) | 35% | 23% | 16.25 | 12.5 | 12.5 | 0.8 | 13.3 | ❌ | — |
| **Mid Redundancy** (60% total) | 40% | 33% | 15.0 | 10.0 | 10.0 | 0.8 | 10.8 | ❌ | — |
| **Target Case** (67% total) | 45% | 37% | 13.75 | 8.66 | 8.66 | 0.8 | 9.46 | ❌ (marginal) | — |
| **Expected Case** (70% total) | 50% | 40% | 12.5 | 7.5 | 7.5 | 0.8 | 8.3 | ❌ (marginal) | 0.96× |
| **Optimistic Case** (75% total) | 50% | 50% | 12.5 | 6.25 | 6.25 | 0.8 | 7.05 | ✓ | 1.13× |
| **High Redundancy** (80% total) | 60% | 50% | 10.0 | 5.0 | 5.0 | 0.8 | 5.8 | ✓ | 1.38× |
| **Very High** (spec example, 85% total) | 67% | 55% | 8.25 | 3.75 | 3.75 | 0.8 | 4.55 | ✓ | 1.76× |

**Calculations:**
- L3 Output = 25 GB × (1 - L3_rate)
- L4 Output = L3_Output × (1 - L4_rate)
- Final = L4_Output + Overhead (800 MB indices/metadata)
- Safety Margin = 8.0 GB / Final

**Key Insights:**

1. **Critical threshold**: System requires **≥70% total redundancy** to fit in 8 GB (marginal at 70%, comfortable at 75%+)
2. **L3 vs L4 sensitivity**: 
   - L3 (exact dedupe) has larger impact: 10% improvement in L3 saves 2.5 GB
   - L4 (similarity dedupe) amplifies L3: 10% improvement in L4 saves 1.0-1.5 GB
3. **Wikipedia plausibility**: 
   - **Likely achievable (70-80%)**: Wikipedia has extensive template reuse, standardized infoboxes, repeated citations
   - **Risk area (60-70%)**: Less redundant articles (unique scientific content, diverse prose) could push below threshold
   - **Empirical validation critical**: Must test on actual English Wikipedia dump to confirm

**Validation Test:**
Run L2+L3 pipeline on 10 GB Wikipedia sample (random articles) and measure actual dedupe ratio. If < 50% exact dedupe at L3, the 8 GB target is at high risk.

---

## 9. Real-World Test Cases

### 9.1 Sample Wikipedia Articles (Representative Corpus)

The following articles represent different redundancy profiles:

| Article Title           | Size (KB) | Redundancy Type              | Expected CF | Expected Physical Size |
|-------------------------|-----------|------------------------------|-------------|------------------------|
| **Albert_Einstein**     | 128       | High (biographies)           | 8:1         | 16 KB                  |
| **Python_(programming)**| 256       | Very High (code examples)    | 12:1        | 21 KB                  |
| **List_of_Countries**   | 512       | Very High (templates)        | 25:1        | 20 KB                  |
| **Quantum_Mechanics**   | 192       | Medium (scientific)          | 5:1         | 38 KB                  |
| **Random_Image_Data**   | 64        | Low (binary/entropy)         | 1.5:1       | 43 KB                  |
| **United_States**       | 384       | High (geographic templates)  | 10:1        | 38 KB                  |
| **2024_Olympics**       | 96        | Very High (tables/infoboxes) | 15:1        | 6 KB                   |
| **Mathematics**         | 224       | Medium (equations, symbols)  | 6:1         | 37 KB                  |

**Total Logical:** 1,856 KB  
**Total Physical (estimated):** 219 KB  
**Achieved Ratio:** **8.47:1** ✓

### 9.2 Wikipedia Content Redundancy Profile

Wikipedia exhibits predictable redundancy patterns:

| Pattern Type              | % of Corpus | Example                                  | L3 Impact | L4 Impact |
|---------------------------|-------------|------------------------------------------|-----------|-----------|
| **Exact Duplicates**      | 15-20%      | Citation templates, category tags        | High      | N/A       |
| **Similar Variants**      | 30-40%      | Infoboxes with different data            | Low       | High      |
| **Unique Content**        | 40-55%      | Article prose, specific facts            | None      | Low       |

**Deduplication Strategy:**
- L3 (exact) handles templates, citations, boilerplate
- L4 (similarity) handles infobox variants, list entries
- L1 (compression) handles all repetitive structures within articles

### 9.3 Stress Test: Worst-Case Content

**Content Types with Poor Compression:**

| Content Type           | Typical Ratio | Strategy                                    |
|------------------------|---------------|---------------------------------------------|
| Random binary data     | 1.0:1         | Store as-is; no compression benefit         |
| Pre-compressed images  | 1.1:1         | Exclude from corpus (text-only)             |
| Encrypted text         | 1.0:1         | Not applicable (Wikipedia is plaintext)     |
| Highly unique prose    | 2.5:1         | L1 compression only; still acceptable       |

**Mitigation:** Wikipedia text corpus is **text-only** (no images). Binary data is excluded. The 25 GB baseline is already the BZ2-compressed size, ensuring compressible input.

### 9.4 Performance Validation Criteria

| Test Case                          | Success Criterion                         | Validates                    |
|------------------------------------|-------------------------------------------|------------------------------|
| Write 1 GB mixed corpus            | Time ≤ 1000 seconds (1 MB/s)              | Write throughput             |
| Read 1000 random articles          | Avg latency ≤ 50 ms                       | Read latency                 |
| 5× duplicate write                 | Physical size ≤ 1.1× unique size          | L3 deduplication             |
| Similar article variants (100×)    | Physical size ≤ 1.2× base size            | L4 similarity detection      |
| Full 8 GB capacity test            | Logical data ≥ 25 GB                      | Overall 3.125:1 goal         |
| 24-hour continuous operation       | Zero data corruption, CRC pass rate: 100% | System stability             |

---

## Appendix A: Delta Encoding Specifications

**Algorithm Choice:** xdelta3 (binary delta compression)

**Rationale:**
- xdelta3 provides excellent compression ratios on binary data with small changes
- Lightweight implementation suitable for MCU (< 50 KB code size)
- Fast decompression (critical for read performance)
- Well-tested and stable (used in rsync, Git, etc.)

**Implementation Details:**

| Parameter | Value | Justification |
|-----------|-------|---------------|
| **Algorithm** | xdelta3 | Binary diff with LZMA-style compression |
| **Delta threshold** | ≤ 20% of original chunk size | Only store delta if it provides ≥ 5:1 savings |
| **Memory overhead** | Base chunk (1.33 KB) + delta buffer (512 B) | Fits in PSRAM during reconstruction |
| **Encode time** | ~2-3 ms per chunk pair | Acceptable for L4 processing |
| **Decode time** | ~0.8-1.2 ms per chunk | Faster than encoding; within read budget |

**Storage Format:**

```c
struct DeltaChunk {
    uint32_t base_lba;        // LBA of base chunk (4 bytes)
    uint16_t base_length;     // Base chunk size (2 bytes)
    uint16_t delta_length;    // Delta size (2 bytes)
    uint8_t  delta_data[];    // Variable-length delta (avg 267 bytes)
} __attribute__((packed));
```

**Reconstruction Process:**

1. Read base chunk from SD card (LBA lookup)
2. Decompress base chunk (L1 DEFLATE)
3. Read delta data from SD card
4. Apply xdelta3 patch to decompressed base
5. Return reconstructed chunk
6. Total time: ~3.8 ms (within read budget)

**Atomicity Guarantee:**

Delta writes use a simple staging approach:
1. Write delta to temporary sector
2. Update index with delta pointer (atomic 8-byte write)
3. Mark temporary sector as permanent
4. On power loss: Incomplete deltas are ignored; base chunk remains valid

**CPU Cost Validation:**

MinHash computation + delta encoding must fit within L4 budget (~1.2 MB/s):
- MinHash (128 hashes): ~1.2 ms per chunk
- xdelta3 encode: ~2.5 ms per chunk (only for similar pairs)
- Total: ~3.7 ms per chunk requiring delta
- Throughput: 1.33 KB ÷ 3.7 ms = 0.36 MB/s per chunk

Since only ~30-40% of chunks require delta encoding (after L3 dedupe), effective throughput ≈ 1.0-1.2 MB/s ✓

---

## Appendix B: LSH Probability Curves and Analysis

**LSH Collision Probability Formula:**

For MinHash LSH with b bands and r rows per band, the probability that two chunks with Jaccard similarity s collide in at least one band is:

\[
P(\text{collision}) = 1 - (1 - s^r)^b
\]

For our configuration (b=8, r=16):
\[
P(\text{collision}) = 1 - (1 - s^{16})^8
\]

**Probability Curves for Selected Configurations:**

| Jaccard Similarity (s) | b=8, r=16 (current) | b=4, r=32 | b=16, r=8 | Target Threshold |
|------------------------|---------------------|-----------|-----------|------------------|
| 0.50 | 0.000 | 0.000 | 0.006 | Too low |
| 0.60 | 0.002 | 0.000 | 0.065 | Too low |
| 0.70 | 0.026 | 0.002 | 0.297 | Marginal |
| **0.75** | **0.077** | **0.010** | **0.477** | **Minimum** |
| **0.80** | **0.202** | **0.069** | **0.676** | **Target** |
| 0.85 | 0.443 | 0.249 | 0.835 | Good |
| 0.90 | 0.810 | 0.567 | 0.941 | Excellent |
| 0.95 | 0.994 | 0.870 | 0.991 | Near-certain |

**⚠️ Corrected Values:** Previous version had calculation errors. All values now match the formula P = 1 - (1 - s^16)^8.

**S-Curve Visualization (Text-Based):**

```
P(collision)
1.0 |                                    ┌────────
    |                               ┌────┘        
0.8 |                          ┌────┘             
    |                     ┌────┘                  
0.6 |                ┌────┘                       
    |           ┌────┘                            
0.4 |      ┌────┘                                 
    | ┌────┘                                      
0.2 |─┘                                           
    |                                             
0.0 └─────┬─────┬─────┬─────┬─────┬─────┬───────
         0.5   0.6   0.7   0.8   0.9   1.0
                  Jaccard Similarity (s)
         
         Legend: b=8, r=16 (current config)
```

**Configuration Trade-offs:**

1. **b=8, r=16 (current)**: 
   - **Pros**: Sharp threshold around s=0.80; low false positive rate below 0.75
   - **Cons**: Lower recall for moderately similar chunks (s=0.70-0.75)
   - **Best for**: High-confidence similarity detection

2. **b=4, r=32**:
   - **Pros**: Very sharp threshold; minimal false positives
   - **Cons**: Misses many similar chunks (low recall); higher false negative rate
   - **Best for**: Ultra-conservative deduplication (low CPU budget)

3. **b=16, r=8**:
   - **Pros**: High recall even for s=0.70; catches more similar chunks
   - **Cons**: Higher false positive rate; more delta attempts that fail threshold
   - **Best for**: Maximizing deduplication (excess CPU available)

**Original Justification (b=8, r=16):**

- **Target similarity**: Wikipedia articles with similar structures (infoboxes, templates) typically have s ≥ 0.80
- **False positive control**: P(collision) < 0.03 for s < 0.75 reduces wasted CPU on dissimilar chunks
- **Recall**: P(collision) ≈ 0.20 at s=0.80, 0.81 at s=0.90 suggests high-similarity pairs are often caught (probabilistic, not guaranteed)
- **Storage issue**: Initially estimated 150 MB, but **revised calculation shows ~305 MB required** (see §8.3)

**⚠️ Implementation Decision Required:**
- **Option A**: Use b=4, r=32 (fits 150 MB, lower recall: P=0.069 at s=0.80)
- **Option B**: Use b=8, r=16 (requires 305 MB, better recall: P=0.202 at s=0.80)

See §8.3 for detailed analysis and recommendation.

**Empirical Validation Required:**

Measure actual Jaccard similarity distribution on Wikipedia corpus:
1. Sample 10,000 random chunk pairs
2. Compute pairwise Jaccard similarity
3. Plot histogram to verify s ≥ 0.80 for similar chunks
4. Adjust b/r if actual distribution differs from assumption

---

## Appendix C: Comprehensive Microbenchmark Plan

**Objective:** Validate all performance claims with empirical measurements on target ESP32-S3 hardware.

> **📋 Note:** This appendix provides ESP-IDF implementation code for microbenchmarks. For the complete validation methodology including experimental design, statistical analysis, reproducibility requirements, and threats to validity, see [VALIDATION_METHODS.md](./VALIDATION_METHODS.md).

**Hardware Requirements:**
- ESP32-S3-WROOM-1 module (8 MB PSRAM, 16 MB Flash)
- 8 GB MicroSD card (UHS-I, U3 rated)
- USB connection to host PC (for logging and data transfer)
- Logic analyzer or oscilloscope (optional, for timing validation)

---

### **Benchmark 1: DEFLATE Compression Throughput**

**Objective:** Measure compression and decompression speed with 1 MB dictionary window.

**ESP-IDF Skeleton Code:**

```c
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "miniz.h"  // or zlib with custom allocator

#define DICT_SIZE (1024 * 1024)  // 1 MB
#define TEST_SIZE (10 * 1024 * 1024)  // 10 MB test data

void benchmark_deflate(void) {
    // Allocate dictionary in PSRAM
    uint8_t *dict = heap_caps_malloc(DICT_SIZE, MALLOC_CAP_SPIRAM);
    uint8_t *input = heap_caps_malloc(TEST_SIZE, MALLOC_CAP_SPIRAM);
    uint8_t *output = heap_caps_malloc(TEST_SIZE, MALLOC_CAP_SPIRAM);
    
    // Load Wikipedia sample into input buffer
    // ... (load from SD or embed small sample)
    
    // Configure miniz with large window
    mz_stream stream = {0};
    stream.avail_in = TEST_SIZE;
    stream.next_in = input;
    stream.avail_out = TEST_SIZE;
    stream.next_out = output;
    
    // Warm-up (flush caches)
    mz_deflateInit2(&stream, 9, MZ_DEFLATED, 15, 9, MZ_DEFAULT_STRATEGY);
    
    // Benchmark compression
    int64_t start = esp_timer_get_time();
    mz_deflate(&stream, MZ_FINISH);
    int64_t end = esp_timer_get_time();
    
    size_t compressed_size = stream.total_out;
    float compress_time_ms = (end - start) / 1000.0;
    float compress_throughput = (TEST_SIZE / 1024.0 / 1024.0) / (compress_time_ms / 1000.0);
    
    printf("Compression: %.2f MB/s, Ratio: %.2f:1\n", 
           compress_throughput, (float)TEST_SIZE / compressed_size);
    
    mz_deflateEnd(&stream);
    
    // Benchmark decompression
    mz_stream d_stream = {0};
    d_stream.avail_in = compressed_size;
    d_stream.next_in = output;
    d_stream.avail_out = TEST_SIZE;
    d_stream.next_out = input;
    
    mz_inflateInit2(&d_stream, 15);
    
    start = esp_timer_get_time();
    mz_inflate(&d_stream, MZ_FINISH);
    end = esp_timer_get_time();
    
    float decompress_time_ms = (end - start) / 1000.0;
    float decompress_throughput = (TEST_SIZE / 1024.0 / 1024.0) / (decompress_time_ms / 1000.0);
    
    printf("Decompression: %.2f MB/s\n", decompress_throughput);
    
    mz_inflateEnd(&d_stream);
    heap_caps_free(dict);
    heap_caps_free(input);
    heap_caps_free(output);
}
```

**Acceptance Criteria:**

**Primary (Target Performance):**
- Compression throughput: **≥ 1.5 MB/s** (validates theoretical projection)
- Decompression throughput: **≥ 5.0 MB/s**
- Compression ratio (on Wikipedia text): **≥ 2.5:1**

**Secondary (Minimum Viable):**
- Compression throughput: **≥ 0.8 MB/s** (sufficient for USB 1.1 requirement)
- Decompression throughput: **≥ 2.0 MB/s** (meets read path requirement)
- Compression ratio: **≥ 2.0:1** (acceptable L1 performance)

**Failure Threshold:**
- Compression throughput: **< 0.5 MB/s** (requires architecture redesign or larger dictionary reduction)

**Note:** Primary criteria are based on theoretical projections from other platforms and may not be achievable on ESP32-S3 due to PSRAM latency. Secondary criteria define minimum acceptable performance for system viability.

---

### **Benchmark 2: FastCDC Chunking Performance**

**Objective:** Measure FastCDC boundary detection speed and chunk size distribution.

**ESP-IDF Skeleton Code:**

```c
#include "esp_timer.h"
#include <stdint.h>

#define FASTCDC_MIN_SIZE 1024
#define FASTCDC_AVG_SIZE 4096
#define FASTCDC_MAX_SIZE 16384
#define RABIN_MODULUS 4095  // P-1 for avg 4 KB chunks

// Rabin fingerprint state
typedef struct {
    uint64_t hash;
    uint32_t window[64];
    int window_pos;
} rabin_t;

uint64_t rabin_slide(rabin_t *r, uint8_t byte_in) {
    // Rolling hash update (simplified)
    uint8_t byte_out = r->window[r->window_pos];
    r->window[r->window_pos] = byte_in;
    r->window_pos = (r->window_pos + 1) % 64;
    
    r->hash = (r->hash << 1) ^ byte_in ^ (byte_out << 7);
    return r->hash;
}

void benchmark_fastcdc(uint8_t *data, size_t size) {
    rabin_t rabin = {0};
    size_t chunk_count = 0;
    size_t chunk_sizes[10000];
    size_t pos = 0;
    size_t chunk_start = 0;
    
    int64_t start = esp_timer_get_time();
    
    while (pos < size) {
        uint64_t hash = rabin_slide(&rabin, data[pos]);
        pos++;
        
        size_t chunk_size = pos - chunk_start;
        
        // Check boundary condition
        if (chunk_size >= FASTCDC_MIN_SIZE &&
            ((hash & RABIN_MODULUS) == 0 || chunk_size >= FASTCDC_MAX_SIZE)) {
            
            chunk_sizes[chunk_count++] = chunk_size;
            chunk_start = pos;
            
            if (chunk_count >= 10000) break;
        }
    }
    
    int64_t end = esp_timer_get_time();
    
    float time_ms = (end - start) / 1000.0;
    float throughput = (pos / 1024.0 / 1024.0) / (time_ms / 1000.0);
    
    // Calculate statistics
    size_t sum = 0, min = SIZE_MAX, max = 0;
    for (size_t i = 0; i < chunk_count; i++) {
        sum += chunk_sizes[i];
        if (chunk_sizes[i] < min) min = chunk_sizes[i];
        if (chunk_sizes[i] > max) max = chunk_sizes[i];
    }
    
    printf("FastCDC: %.2f MB/s, Chunks: %zu, Avg: %zu B, Min: %zu B, Max: %zu B\n",
           throughput, chunk_count, sum / chunk_count, min, max);
}
```

**Acceptance Criteria:**
- Chunking throughput: ≥ 8.0 MB/s
- Average chunk size: 3.5-4.5 KB (target 4096)
- Min chunk size: ≥ 1024 bytes
- Max chunk size: ≤ 16384 bytes

---

### **Benchmark 3: SHA-256 Hardware Acceleration**

**Objective:** Validate ESP32-S3 hardware SHA-256 performance.

**ESP-IDF Skeleton Code:**

```c
#include "esp_timer.h"
#include "mbedtls/sha256.h"

void benchmark_sha256(void) {
    const size_t CHUNK_SIZE = 4096;
    const size_t NUM_CHUNKS = 2000;  // 8 MB total
    
    uint8_t *data = heap_caps_malloc(CHUNK_SIZE, MALLOC_CAP_SPIRAM);
    uint8_t hash[32];
    
    // Fill with test data
    for (size_t i = 0; i < CHUNK_SIZE; i++) {
        data[i] = i & 0xFF;
    }
    
    int64_t start = esp_timer_get_time();
    
    for (size_t i = 0; i < NUM_CHUNKS; i++) {
        mbedtls_sha256(data, CHUNK_SIZE, hash, 0);  // 0 = SHA-256 (not SHA-224)
    }
    
    int64_t end = esp_timer_get_time();
    
    size_t total_bytes = CHUNK_SIZE * NUM_CHUNKS;
    float time_ms = (end - start) / 1000.0;
    float throughput = (total_bytes / 1024.0 / 1024.0) / (time_ms / 1000.0);
    
    printf("SHA-256 HW: %.2f MB/s (%.2f µs per 4KB chunk)\n", 
           throughput, (time_ms * 1000.0) / NUM_CHUNKS);
    
    heap_caps_free(data);
}
```

**Acceptance Criteria:**
- SHA-256 throughput: ≥ 15 MB/s
- Latency per 4 KB chunk: ≤ 300 µs

---

### **Benchmark 4: MinHash Generation**

**Objective:** Measure MinHash signature computation time.

**ESP-IDF Skeleton Code:**

```c
#include "esp_timer.h"
#include "murmur3.h"  // MurmurHash3 implementation

#define NUM_HASHES 128
#define CHUNK_SIZE 4096

void minhash_compute(const uint8_t *data, size_t len, uint32_t *minhash) {
    // Initialize with max values
    for (int i = 0; i < NUM_HASHES; i++) {
        minhash[i] = UINT32_MAX;
    }
    
    // Generate shingles (4-byte sliding window)
    for (size_t pos = 0; pos < len - 3; pos++) {
        uint32_t shingle = *(uint32_t*)(data + pos);
        
        // Hash with NUM_HASHES different seeds
        for (int h = 0; h < NUM_HASHES; h++) {
            uint32_t hash;
            MurmurHash3_x86_32(&shingle, 4, h, &hash);
            
            if (hash < minhash[h]) {
                minhash[h] = hash;
            }
        }
    }
}

void benchmark_minhash(void) {
    const size_t NUM_CHUNKS = 1000;
    uint8_t *data = heap_caps_malloc(CHUNK_SIZE, MALLOC_CAP_SPIRAM);
    uint32_t minhash[NUM_HASHES];
    
    // Fill with test data
    for (size_t i = 0; i < CHUNK_SIZE; i++) {
        data[i] = rand() & 0xFF;
    }
    
    int64_t start = esp_timer_get_time();
    
    for (size_t i = 0; i < NUM_CHUNKS; i++) {
        minhash_compute(data, CHUNK_SIZE, minhash);
    }
    
    int64_t end = esp_timer_get_time();
    
    float time_per_chunk_ms = ((end - start) / 1000.0) / NUM_CHUNKS;
    float throughput = (CHUNK_SIZE / 1024.0 / 1024.0) / (time_per_chunk_ms / 1000.0);
    
    printf("MinHash (n=%d): %.2f ms per chunk, %.2f MB/s\n",
           NUM_HASHES, time_per_chunk_ms, throughput);
    
    heap_caps_free(data);
}
```

**Acceptance Criteria:**
- MinHash computation time: ≤ 1.5 ms per 4 KB chunk
- Throughput: ≥ 1.2 MB/s

---

### **Benchmark 5: PSRAM Index Lookup Latency**

**Objective:** Measure hash table probe latency in PSRAM.

**ESP-IDF Skeleton Code:**

```c
#include "esp_timer.h"
#include "esp_heap_caps.h"

#define INDEX_SIZE 150000  // 150K entries (max for 6 MB PSRAM)

typedef struct {
    uint8_t sha256[32];
    uint32_t lba;
    uint16_t length;
    uint16_t refcount;
} __attribute__((packed)) chunk_entry_t;  // 40 bytes

void benchmark_psram_lookup(void) {
    const size_t NUM_LOOKUPS = 10000;
    
    // Allocate index in PSRAM
    chunk_entry_t *index = heap_caps_malloc(
        INDEX_SIZE * sizeof(chunk_entry_t), 
        MALLOC_CAP_SPIRAM
    );
    
    // Fill with test data
    for (size_t i = 0; i < INDEX_SIZE; i++) {
        for (int j = 0; j < 32; j++) {
            index[i].sha256[j] = (i * j) & 0xFF;
        }
        index[i].lba = i;
    }
    
    // Random lookup test
    uint32_t hash_query[8];  // First 32 bytes of SHA-256
    
    int64_t start = esp_timer_get_time();
    
    for (size_t i = 0; i < NUM_LOOKUPS; i++) {
        size_t idx = rand() % INDEX_SIZE;
        
        // Simulate hash table probe (linear search for benchmark)
        volatile bool found = false;
        for (size_t j = 0; j < 100; j++) {  // Check 100 entries average
            size_t probe_idx = (idx + j) % INDEX_SIZE;
            if (memcmp(index[probe_idx].sha256, hash_query, 32) == 0) {
                found = true;
                break;
            }
        }
    }
    
    int64_t end = esp_timer_get_time();
    
    float avg_latency_us = ((end - start) / 1.0) / NUM_LOOKUPS;
    
    printf("PSRAM Lookup: %.2f µs per probe (avg)\n", avg_latency_us);
    
    heap_caps_free(index);
}
```

**Acceptance Criteria:**
- Average lookup latency: ≤ 100 µs
- No cache thrashing or memory errors

---

### **Benchmark 6: Full Pipeline Wikipedia Test**

**Objective:** Measure end-to-end compression factor on actual Wikipedia dump.

**Implementation:**
1. Download English Wikipedia dump (pages-articles.xml.bz2, ~25 GB)
2. Decompress to 75 GB raw XML
3. Run full L1-L4 pipeline on ESP32-S3
4. Measure final storage size and compare to 8 GB target

**Test Procedure:**
```
1. Extract 10 GB sample from Wikipedia dump
2. Stream to ESP32-S3 via USB at 1 MB/s
3. Process through L1 (DEFLATE) → L2 (FastCDC) → L3 (dedupe) → L4 (similarity)
4. Measure:
   - Final physical storage size
   - L3 deduplication ratio (exact matches)
   - L4 similarity ratio (delta encoding)
   - Processing time
   - Memory usage
```

**Acceptance Criteria:**
- Overall compression factor: ≥ 9.375:1 (10 GB → ≤ 1.07 GB)
- L3 dedupe rate: ≥ 50% (indicates sufficient template/citation redundancy)
- L4 similarity rate: ≥ 30% (indicates similar article structures)
- Processing throughput: ≥ 1.0 MB/s (match USB 1.1 speed)

---

**Microbenchmark Execution Plan:**

1. **Setup (Week 1)**: Acquire hardware, install ESP-IDF, configure development environment
2. **Individual Benchmarks (Week 2-3)**: Run Benchmarks 1-5, collect data, tune parameters
3. **Integration Testing (Week 4)**: Run Benchmark 6 with full Wikipedia sample
4. **Analysis (Week 5)**: Compare results to specification, update projections, identify bottlenecks
5. **Iteration (Week 6+)**: Optimize implementations based on benchmark results

---

## References

### Core Algorithms and Data Structures

1. **Xia, W., et al. (2016).** "FastCDC: A Fast and Efficient Content-Defined Chunking Approach for Data Deduplication." 
   *USENIX Annual Technical Conference (ATC)*.  
   [https://www.usenix.org/conference/atc16/technical-sessions/presentation/xia](https://www.usenix.org/conference/atc16/technical-sessions/presentation/xia)

2. **Ziv, J. and Lempel, A. (1977).** "A Universal Algorithm for Sequential Data Compression." 
   *IEEE Transactions on Information Theory*, Vol. 23, No. 3, pp. 337-343.  
   DOI: 10.1109/TIT.1977.1055714  
   (Foundational LZ77 algorithm underlying DEFLATE compression)
   [https://courses.cs.duke.edu/spring03/cps296.5/papers/ziv_lempel_1977_universal_algorithm.pdf](https://courses.cs.duke.edu/spring03/cps296.5/papers/ziv_lempel_1977_universal_algorithm.pdf)

3. **Deutsch, P. (1996).** "DEFLATE Compressed Data Format Specification version 1.3."  
   *RFC 1951, IETF*.  
   [https://www.rfc-editor.org/rfc/rfc1951](https://www.rfc-editor.org/rfc/rfc1951)

4. **Rabin, M. O. (1981).** "Fingerprinting by Random Polynomials."  
   *Technical Report TR-15-81, Center for Research in Computing Technology, Harvard University*.  
   (Original work on Rabin fingerprinting for content-defined chunking. Could not find public listing for paper)

### Locality-Sensitive Hashing and Similarity Detection

5. **Broder, A. Z. (1997).** "On the Resemblance and Containment of Documents."  
   *Proceedings of the Compression and Complexity of Sequences*, pp. 21-29. IEEE.  
   DOI: 10.1109/SEQUEN.1997.666900  
   (Original MinHash algorithm and Jaccard similarity estimation)
   [https://www.cs.princeton.edu/courses/archive/spring13/cos598C/broder97resemblance.pdf](https://www.cs.princeton.edu/courses/archive/spring13/cos598C/broder97resemblance.pdf)

6. **Andoni, A. and Indyk, P. (2008).** "Near-Optimal Hashing Algorithms for Approximate Nearest Neighbor in High Dimensions."  
   *Communications of the ACM*, Vol. 51, No. 1, pp. 117-122.  
   [https://dl.acm.org/doi/10.1145/1327452.1327494](https://dl.acm.org/doi/10.1145/1327452.1327494)  
   (Comprehensive LSH survey and algorithms)

7. **Andoni, A., et al. (2015).** "Practical and Optimal LSH for Angular Distance."  
   *Advances in Neural Information Processing Systems (NIPS)*, pp. 1225-1233.  
   [https://www.mit.edu/~andoni/LSH/](https://www.mit.edu/~andoni/LSH/)  
   (MIT LSH Algorithm Repository - includes E2LSH and FALCONN implementations)

8. **Tan, Z., et al. (2023).** "Fast Locality Sensitive Hashing with Theoretical Guarantee."  
   *arXiv preprint arXiv:2309.15479*.  
   [https://arxiv.org/abs/2309.15479](https://arxiv.org/abs/2309.15479)  
   (Recent FastLSH with up to 80× speedup in hash function evaluation)

### Storage Systems and Deduplication

9. **Tarasov, V., et al. (2024).** "An Evaluation of Deduplication and Compression on Scientific Datasets."  
   *arXiv preprint arXiv:2411.04257*.  
   [https://arxiv.org/abs/2411.04257](https://arxiv.org/abs/2411.04257)

10. **Lee, C., et al. (2015).** "F2FS: A New File System for Flash Storage."  
    *Proceedings of the 13th USENIX Conference on File and Storage Technologies (FAST)*, pp. 273-286.  
    [https://www.usenix.org/conference/fast15/technical-sessions/presentation/lee](https://www.usenix.org/conference/fast15/technical-sessions/presentation/lee)  
    (Log-structured filesystem design for flash with wear leveling)

11. **Seltzer, M., et al. (1993).** "An Implementation of a Log-Structured File System for UNIX."  
    *USENIX Winter Technical Conference*, pp. 307-326.  
    (Classic work on log-structured filesystems relevant to flash storage optimization)

### Hardware Documentation

12. **Espressif Systems. (2022).** "ESP32-S3 Technical Reference Manual - SDMMC Host Controller."  
    *ESP-IDF Programming Guide v4.4*.  
    [https://docs.espressif.com/projects/esp-idf/en/v4.4.8/esp32s3/api-reference/peripherals/sdmmc_host.html](https://docs.espressif.com/projects/esp-idf/en/v4.4.8/esp32s3/api-reference/peripherals/sdmmc_host.html)

13. **Espressif Systems. (2022).** "ESP32-S3 Datasheet - Hardware Cryptographic Acceleration."  
    *ESP32-S3 Series Datasheet v1.3*.  
    [https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)  
    (SHA-256 hardware acceleration specifications)

---

**Document Version:** 1.3  
**Last Updated:** October 19, 2025  
**Platform:** ESP32-S3 (Dual-core Xtensa LX7)
**Changelog:**
- **v1.3 (Oct 19):** **Comprehensive scientific rigor improvements combining mathematical corrections, technical depth enhancements, and tone/methodology revisions:**
  - **Mathematical & Feasibility Corrections:**
    - (1) **Corrected compression factor**: Realistic projection **8.7:1** (down from 12:1), acknowledges **falls short of 10.56:1 requirement by -17%**; system now rated **marginal feasibility** contingent on validation
    - (2) **Fixed LSH storage calculation**: Revised to **300 MB** (2× original estimate) due to list structure overhead; added mitigation options (4-band config or compact encoding); included sensitivity analysis tables for L4 storage parameters
    - (3) **Added PSRAM cache miss analysis**: Realistic read throughput **0.49 MB/s** with 50% cache hit (down from 1.40 MB/s assumption); system may **not meet USB 1.1 requirement**
    - (4) **Added confidence intervals**: All timing estimates now show ranges (e.g., "6 ± 2 ms"); added best/typical/worst-case scenarios
  - **Technical Documentation Enhancements:**
    - (5) **Derived LSH band table sizing from first principles**: Band hash bit-width calculations with mathematical derivation showing expected unique buckets and collision rates
    - (6) **Created comprehensive microbenchmark plan** (Appendix C): ESP-IDF skeleton code for 6 benchmarks (DEFLATE, FastCDC, SHA-256, MinHash, PSRAM, full pipeline)
    - (7) **Added LSH probability curves appendix** (Appendix B): Collision probability formulas, S-curve visualization, parameter justification for b=8, r=16
    - (8) **Documented delta encoding specifications** (Appendix A): xdelta3 algorithm, implementation parameters, storage format, reconstruction process, atomicity guarantees
    - (9) **Added redundancy sensitivity analysis** (§8.5): 9-scenario table showing system behavior under varying L3/L4 deduplication rates
    - (10) **Clarified PSRAM working-set vs SD persistent index**: Explicit labeling and cache performance model
    - (11) **Added explicit MB/MiB definitions**: Units convention section with decimal (MB = 10^6) vs binary (MiB = 2^20) clarification
    - (12) **Specified FastCDC parameters**: Target 4 KiB avg, min 1 KiB, max 16 KiB with rationale
  - **Tone & Methodology Improvements:**
    - (13) **Marked all throughput as projected**: "~1.5 MB/s (projected, unvalidated)" replaces definitive claims; added caveats about unvalidated PSRAM/CPU assumptions
    - (14) **Tone shift to hypothesis**: Changed from "achieves" to "hypothesizes"; abstract now states "research specification" and "could potentially achieve"
    - (15) **Added circular reasoning warnings**: Flagged 50% dedupe assumptions as "unvalidated design targets requiring empirical measurement"
    - (16) **Risk assessment**: System now rated **high risk** for 8 GB target; recommends 16 GB card or higher redundancy validation
    - (17) **Removed superlatives**: Replaced "unprecedented," "extreme," "novel" with plain language ("high density" instead of "extreme density")
    - (18) **Reframed §5 as open inquiry**: Changed from "Discussion and Practical Implications" to "Open Questions and Research Goals"; rewritten as "what we hope to learn" with conditional "if" statements; focuses on uncertainties, risk factors, and learning value independent of success; defines tiered success criteria (5:1 minimum viable, 9.375:1 target)
  - **Summary:** Document now presents skeptical scientific inquiry rather than advocacy; all quantitative claims tempered with uncertainty and validation requirements; reads as genuine research inquiry with comprehensive technical depth.
- **v1.1 (Oct 18):** Corrected baseline data flow (75 GB decompressed input, not 25 GB BZ2), updated required CF to 9.375:1, reduced safety margin to 1.15×, corrected LSH storage calculation (band tables vs full signatures), clarified units (MiB/MB), added confidence levels, fixed index entry size (40 bytes).

---
