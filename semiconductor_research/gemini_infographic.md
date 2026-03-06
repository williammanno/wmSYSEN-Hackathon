<p align="center">
  <strong>OmniLogix AI</strong> Live Dashboard
</p>

<p align="center">
  Real-time synthetic data augmentation for tracking semiconductor supply chains across trans-Pacific routes.<br>
  Monitoring Intel, Nvidia, and Broadcom logistics.
</p>

<p align="center">
  <a href="https://gemini.google.com/share/db1f1be5ba57"><strong>View the full interactive infographic →</strong></a>
</p>

---

## Key Metrics

| | **Active Shipments** | **Avg Transit Delay** | **Synthetic Threat Index** | **AI Confidence** |
|:---:|:---:|:---:|:---:|:---:|
| **Value** | **1,248** | **1.4 Days** | **72/100** | **94.6%** |
| **Status** | ▲ 12% vs Last Week | Synthetic Risk Elevated | Typhoon Warning Active | Model Re-trained 2h ago |

---

## Trans-Pacific Node Architecture

The global semiconductor supply chain is highly segmented. Raw silicon processing and advanced fabrication primarily occur in Asian foundries. Final assembly, testing, and distribution for major tech giants are strategically split between Asian hubs and domestic US facilities to mitigate geopolitical and logistical friction.

```mermaid
flowchart TB
    subgraph Asia["Asia Mfg & Fab Sites"]
        NB["Nvidia & Broadcom: Taiwan Hsinchu, Taoyuan"]
        IntelA["Intel: Malaysia Penang, Vietnam Ho Chi Minh"]
    end

    subgraph Transport["Transport"]
        direction LR
        Air["Air Freight 14-24 hrs"]
        Ocean["Ocean Freight 15-30 days"]
    end

    subgraph US["US Assembly & Dist Hubs"]
        IntelU["Intel: Chandler AZ, New Albany OH"]
        NvidiaU["Nvidia: Santa Clara CA, Austin TX"]
        BroadcomU["Broadcom: San Jose CA, Irvine CA"]
    end

    Asia --> Air
    Asia --> Ocean
    Air --> US
    Ocean --> US
```

### Asia Mfg & Fab Sites

| Company | Location | Function |
|---------|----------|----------|
| **Nvidia & Broadcom** | 🇹🇼 Hsinchu, Taiwan | TSMC Fab |
| **Nvidia & Broadcom** | 🇹🇼 Taoyuan, Taiwan | Assembly |
| **Intel** | 🇲🇾 Penang, Malaysia | Assembly/Test |
| **Intel** | 🇻🇳 Ho Chi Minh, Vietnam | Assembly |

### US Assembly & Dist Hubs

| Company | Location | Function |
|---------|----------|----------|
| **Intel** | 🇺🇸 Chandler, AZ | Fab/Assembly |
| **Intel** | 🇺🇸 New Albany, OH | Mega-Fab Building |
| **Nvidia** | 🇺🇸 Santa Clara, CA | HQ/Distribution |
| **Nvidia** | 🇺🇸 Austin, TX | Logistics Hub |
| **Broadcom** | 🇺🇸 San Jose, CA | Dist/Config |
| **Broadcom** | 🇺🇸 Irvine, CA | Logistics Hub |

---

## Logistics Volume Distribution

*Comparing the proportion of manufacturing and assembly loads processed per week across key geographic sectors.*

**Relative Volume Load** (stacked by company)

| Region | Nvidia | Broadcom | Intel | Total |
|--------|:------:|:--------:|:-----:|:-----:|
| Taiwan (TSMC/Foxconn) | 85 | 75 | 20 | 180 |
| Malaysia (Intel Assembly) | 5 | 10 | 90 | 105 |
| US West Coast Hubs | 60 | 50 | 30 | 140 |
| US Inland Facilities | 20 | 15 | 80 | 115 |

*Stacked breakdown: Nvidia (purple) | Broadcom (pink) | Intel (cyan)*

---

## Transit Efficiency Profile

*Analyzing route cost versus transit time. Bubble size indicates total shipped volume in metric tons.*

| Route | Transit Time (Days) | Cost per Ton (USD) | Relative Volume |
|-------|:------------------:|:------------------:|:---------------:|
| Taipei → SFO (Air) | 1.5 | $8,500 | Small |
| Kaohsiung → LAX (Ocean) | 22.0 | $1,200 | Large |
| Penang → AZ (Air) | 2.0 | $9,200 | Small |
| Penang → LAX (Ocean) | 28.0 | $1,100 | Medium |

---

## Synthetic Data Augmentation Matrix

Traditional historical models fail during unprecedented global events. By injecting dynamic synthetic data—such as simulated typhoon landfalls in the South China Sea, unannounced port labor strikes in Long Beach, and sudden geopolitical tariff implementations—our AI trains robust predictive algorithms capable of preemptive rerouting.

### Risk Factor Sensitivity

*Radar analysis shows how strongly current supply chain node configurations react to distinct categories of synthetic environmental and political stress injections.*

| Risk Factor | Current Operations Profile | AI Simulated Maximum Stress |
|-------------|:--------------------------:|:---------------------------:|
| Typhoon / Extreme Weather | 45 | 95 |
| Port Labor Strikes | 60 | 85 |
| Tariff Imposition | 30 | 90 |
| Air Freight Fuel Spike | 80 | 95 |
| Geopolitical Blockades | 20 | 100 |

### Predictive Delay Modeling

*Live AI performance. The chart contrasts standard expected delivery timelines against AI-predicted delays after injecting live weather anomaly and port congestion synthetic data streams.*

**Cumulative Delay (Hours)**

| Day | Standard Baseline (Hours Delay) | AI Predicted Delay (Post-Synthetic Injection) |
|-----|:------------------------------:|:--------------------------------------------:|
| Day 1 | 2 | 2 |
| Day 2 | 3 | 5 |
| Day 3 | 2 | 12 |
| Day 4 | 4 | 24 |
| Day 5 | 3 | 38 |
| Day 6 | 5 | 42 |
| Day 7 | 4 | 35 |

```mermaid
xychart
    title "Predictive Delay: Baseline vs AI-Predicted"
    x-axis [Day 1, Day 2, Day 3, Day 4, Day 5, Day 6, Day 7]
    y-axis "Cumulative Delay (Hours)" 0 --> 50
    line "Standard Baseline" [2, 3, 2, 4, 3, 5, 4]
    line "AI Predicted (Post-Synthetic)" [2, 5, 12, 24, 38, 42, 35]
```

---

## Methodology Notes

| Item | Details |
|------|---------|
| **Palette** | Vibrant Cyber/Neon (Background: `#0f172a`, Accents: `#06b6d4` cyan, `#ec4899` pink, `#8b5cf6` purple, `#f59e0b` amber) |
| **Plan Summary** | 1. Global Network overview (HTML grid), 2. Volume & Transit analysis (Bar/Bubble charts), 3. Synthetic Data injection impact (Radar/Line charts) |
| **Chart Choices** | Stacked Bar for Volume (compare parts to whole), Bubble for Transit (relationships between Cost/Time/Vol), Radar for Risk (multivariate factors), Line for Delay Modeling (change over time) |
| **Color Legend** | Intel = Cyan, Nvidia = Purple, Broadcom = Pink |

---

> **Other versions:** [Original Gemini infographic](https://gemini.google.com/share/db1f1be5ba57) | `gemini_infographic.html` — local HTML dashboard with Chart.js (open in browser)
