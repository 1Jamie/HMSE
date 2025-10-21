#!/usr/bin/env python3
"""
HMSE Energy Break-Even Calculator

Calculates total system energy (compression + transmission) and determines
break-even compression factors for different bandwidth scenarios.

Usage:
    python energy_calculator.py --size 75 --cf 9.375 --bandwidth 1 --transmit-power 5
    python energy_calculator.py --size 75 --cf 5.0 --bandwidth 0.05 --transmit-power 0.5 --plot

Author: HMSE Project
License: CC BY-NC-SA 4.0
"""

import argparse
import sys

try:
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False
    print("Warning: matplotlib/numpy not installed. Plotting disabled.", file=sys.stderr)
    print("Install with: pip install matplotlib numpy", file=sys.stderr)

def calculate_energy(size_gb, cf, bandwidth_mbps, 
                     compress_power_w=0.5, compress_time_hrs=36, 
                     transmit_power_w=5):
    """
    Calculate total energy for compression + transmission.
    
    Args:
        size_gb: Data size in GB
        cf: Compression factor
        bandwidth_mbps: Transmission bandwidth in Mbps
        compress_power_w: Compression power in watts
        compress_time_hrs: Compression time in hours
        transmit_power_w: Transmission power in watts
    
    Returns:
        Dictionary with energy breakdown
    """
    # Convert to consistent units
    size_bits = size_gb * 8e9  # GB to bits
    bandwidth_bps = bandwidth_mbps * 1e6  # Mbps to bps
    
    # Compression energy (constant for given size)
    e_compress = compress_power_w * compress_time_hrs  # Wh
    
    # Transmission energy (depends on CF)
    transmit_time_hrs = (size_bits / cf / bandwidth_bps) / 3600
    e_transmit = transmit_power_w * transmit_time_hrs  # Wh
    
    # Total energy
    e_total = e_compress + e_transmit
    
    return {
        'compression_energy_wh': e_compress,
        'transmission_energy_wh': e_transmit,
        'total_energy_wh': e_total,
        'transmission_time_hrs': transmit_time_hrs
    }

def find_breakeven_cf(size_gb, bandwidth_mbps, 
                      compress_power_w=0.5, compress_time_hrs=36, 
                      transmit_power_w=5):
    """
    Find the break-even compression factor where total energy with compression
    equals transmission-only energy (no compression).
    """
    size_bits = size_gb * 8e9
    bandwidth_bps = bandwidth_mbps * 1e6
    
    # Energy without compression (CF = 1.0)
    e_uncompressed = transmit_power_w * (size_bits / bandwidth_bps) / 3600
    
    # Energy of compression (constant)
    e_compress = compress_power_w * compress_time_hrs
    
    # Solve for CF where total = uncompressed
    # e_compress + (transmit_power × size / (CF × BW) / 3600) = e_uncompressed
    # Rearrange:
    # CF = e_uncompressed / (e_uncompressed - e_compress)
    
    if e_compress >= e_uncompressed:
        return float('inf')  # Compression never breaks even
    
    cf_breakeven = e_uncompressed / (e_uncompressed - e_compress)
    
    return cf_breakeven

def plot_energy_curve(size_gb, bandwidth_mbps, compress_power_w=0.5,
                      compress_time_hrs=36, transmit_power_w=5, max_cf=15):
    """Generate energy vs. compression factor plot."""
    if not HAS_PLOT:
        print("Error: Plotting requires matplotlib and numpy", file=sys.stderr)
        return
    
    cfs = np.linspace(1.0, max_cf, 1000)
    results = [calculate_energy(size_gb, cf, bandwidth_mbps, compress_power_w,
                                compress_time_hrs, transmit_power_w) 
               for cf in cfs]
    energies = [r['total_energy_wh'] for r in results]
    e_compress_const = compress_power_w * compress_time_hrs
    e_transmits = [r['transmission_energy_wh'] for r in results]
    
    e_uncompressed = calculate_energy(size_gb, 1.0, bandwidth_mbps, 
                                      compress_power_w, compress_time_hrs, 
                                      transmit_power_w)['total_energy_wh']
    cf_breakeven = find_breakeven_cf(size_gb, bandwidth_mbps, compress_power_w,
                                      compress_time_hrs, transmit_power_w)
    
    plt.figure(figsize=(12, 7))
    
    # Plot transmission energy (decreases with CF)
    plt.fill_between(cfs, 0, e_transmits, alpha=0.3, color='red', 
                     label='Transmission Energy')
    
    # Plot compression energy (constant)
    plt.fill_between(cfs, e_transmits, 
                     [e + e_compress_const for e in e_transmits],
                     alpha=0.3, color='blue', label='Compression Energy')
    
    # Plot total energy line
    plt.plot(cfs, energies, 'b-', linewidth=2, label='Total Energy')
    
    # Mark uncompressed baseline
    plt.axhline(e_uncompressed, color='r', linestyle='--', linewidth=2,
                label=f'No Compression ({e_uncompressed:.0f} Wh)')
    
    # Mark break-even point
    if cf_breakeven < max_cf:
        plt.axvline(cf_breakeven, color='g', linestyle='--', linewidth=2,
                    label=f'Break-even ({cf_breakeven:.3f}:1)')
    
    # Mark 5:1 threshold
    plt.axvline(5.0, color='orange', linestyle=':', linewidth=2,
                label='5:1 "Useful" Threshold')
    
    plt.xlabel('Compression Factor', fontsize=14, fontweight='bold')
    plt.ylabel('Total Energy (Wh)', fontsize=14, fontweight='bold')
    plt.title(f'Energy Consumption vs. Compression Factor\n'
              f'{size_gb} GB corpus, {bandwidth_mbps} Mbps downlink, '
              f'{transmit_power_w}W transmitter', 
              fontsize=16, fontweight='bold')
    plt.legend(fontsize=11, loc='upper right')
    plt.grid(alpha=0.3, linestyle='--')
    plt.xlim(1, max_cf)
    plt.ylim(0, max(energies) * 1.1)
    
    # Add annotations
    if cf_breakeven < max_cf:
        plt.annotate(f'CF > {cf_breakeven:.3f}:1\nsaves energy',
                    xy=(cf_breakeven + 0.5, e_uncompressed * 0.8),
                    fontsize=10, color='green', fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('energy_curve.png', dpi=150, bbox_inches='tight')
    print("📊 Plot saved to energy_curve.png")

def main():
    parser = argparse.ArgumentParser(
        description='HMSE Energy Break-Even Calculator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Satellite scenario (1 Mbps, 5W transmitter)
  python energy_calculator.py --size 75 --cf 9.375 --bandwidth 1 --transmit-power 5
  
  # LoRaWAN scenario (50 kbps, 0.5W transmitter)
  python energy_calculator.py --size 75 --cf 5.0 --bandwidth 0.05 --transmit-power 0.5
  
  # Generate plot
  python energy_calculator.py --size 75 --cf 9.375 --bandwidth 1 --transmit-power 5 --plot
        """)
    
    parser.add_argument('--size', type=float, required=True, 
                       help='Data size (GB)')
    parser.add_argument('--cf', type=float, required=True, 
                       help='Compression factor (e.g., 9.375 for 9.375:1)')
    parser.add_argument('--bandwidth', type=float, required=True, 
                       help='Transmission bandwidth (Mbps)')
    parser.add_argument('--transmit-power', type=float, default=5, 
                       help='Transmission power (W, default: 5)')
    parser.add_argument('--compress-power', type=float, default=0.5,
                       help='Compression power (W, default: 0.5)')
    parser.add_argument('--compress-time', type=float, default=36,
                       help='Compression time (hours, default: 36)')
    parser.add_argument('--plot', action='store_true', 
                       help='Generate energy curve plot')
    
    args = parser.parse_args()
    
    # Calculate energy for given scenario
    result = calculate_energy(args.size, args.cf, args.bandwidth,
                              args.compress_power, args.compress_time, 
                              args.transmit_power)
    
    # Calculate energy without compression
    result_no_compress = calculate_energy(args.size, 1.0, args.bandwidth,
                                          args.compress_power, args.compress_time,
                                          args.transmit_power)
    
    # Find break-even CF
    cf_breakeven = find_breakeven_cf(args.size, args.bandwidth, 
                                      args.compress_power, args.compress_time,
                                      args.transmit_power)
    
    # Calculate ROI
    energy_saved = result_no_compress['total_energy_wh'] - result['total_energy_wh']
    roi = energy_saved / result['compression_energy_wh'] if result['compression_energy_wh'] > 0 else 0
    
    # Print results
    print(f"\n{'='*70}")
    print(f"  HMSE Energy Analysis")
    print(f"{'='*70}")
    print(f"\n📊 Scenario Parameters:")
    print(f"  Corpus Size:          {args.size} GB")
    print(f"  Compression Factor:   {args.cf}:1")
    print(f"  Transmission BW:      {args.bandwidth} Mbps")
    print(f"  Transmit Power:       {args.transmit_power} W")
    print(f"  Compress Power:       {args.compress_power} W")
    print(f"  Compress Time:        {args.compress_time} hours")
    
    print(f"\n⚡ Energy Breakdown (WITH Compression):")
    print(f"  Compression Energy:   {result['compression_energy_wh']:.1f} Wh")
    print(f"  Transmission Energy:  {result['transmission_energy_wh']:.1f} Wh")
    print(f"  Total Energy:         {result['total_energy_wh']:.1f} Wh")
    print(f"  Transmission Time:    {result['transmission_time_hrs']:.2f} hours")
    
    print(f"\n⚡ Energy (NO Compression, CF=1.0):")
    print(f"  Transmission Energy:  {result_no_compress['transmission_energy_wh']:.1f} Wh")
    print(f"  Total Energy:         {result_no_compress['total_energy_wh']:.1f} Wh")
    
    print(f"\n💰 Energy Economics:")
    print(f"  Break-even CF:        {cf_breakeven:.3f}:1")
    print(f"  Safety Margin:        {args.cf / cf_breakeven:.2f}×")
    print(f"  Energy Saved:         {energy_saved:.1f} Wh ({100*energy_saved/result_no_compress['total_energy_wh']:.1f}%)")
    print(f"  Energy ROI:           {roi:.1f}× (every 1 Wh spent saves {roi:.1f} Wh)")
    
    # Interpretation
    print(f"\n💡 Interpretation:")
    if args.cf > cf_breakeven:
        margin = args.cf / cf_breakeven
        print(f"  ✅ Compression is energy-positive with {margin:.1f}× safety margin")
        if roi >= 36:
            print(f"  ✅ ROI ≥ 36×: Multi-layer complexity justified")
        elif roi >= 20:
            print(f"  ⚠️  ROI {roi:.0f}×: Moderate returns, simpler algorithms may suffice")
        else:
            print(f"  ⚠️  ROI {roi:.0f}×: Low returns, reconsider complexity")
    else:
        print(f"  ❌ Compression overhead exceeds transmission savings")
        print(f"  ❌ Need CF ≥ {cf_breakeven:.3f}:1 to break even")
    
    print(f"\n{'='*70}\n")
    
    # Generate plot if requested
    if args.plot:
        plot_energy_curve(args.size, args.bandwidth, args.compress_power,
                         args.compress_time, args.transmit_power)

if __name__ == '__main__':
    main()


