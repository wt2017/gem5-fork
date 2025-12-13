#!/usr/bin/env python3

"""
Full System (FS) mode configuration for running shm_rw program.
This script uses the X86DemoBoard to boot Ubuntu and run the shm_rw program
which requires direct physical memory access.

Usage:
    ./build/X86/gem5.opt configs/learning_gem5/part1/shm_fs.py

The script will:
1. Boot Ubuntu 24.04 in FS mode
2. Wait for login prompt
3. Provide instructions for running shm_rw
"""

import m5
from m5.objects import *
from gem5.prebuilt.demo.x86_demo_board import X86DemoBoard
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
from gem5.isas import ISA
from gem5.utils.requires import requires
from gem5.components.processors.cpu_types import CPUTypes

# Check if X86 ISA is available
requires(isa_required=ISA.X86)

print("Setting up Full System simulation for shm_rw program...")

# Create a custom X86 board with Atomic CPU for faster simulation
from gem5.components.boards.x86_board import X86Board
from gem5.components.cachehierarchies.classic.private_l1_shared_l2_cache_hierarchy import (
    PrivateL1SharedL2CacheHierarchy,
)
from gem5.components.memory.multi_channel import DualChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor

# Create custom board with Atomic CPU (much faster than Timing for FS mode)
memory = DualChannelDDR4_2400(size="3GiB")
processor = SimpleProcessor(
    cpu_type=CPUTypes.ATOMIC, isa=ISA.X86, num_cores=2
)
cache_hierarchy = PrivateL1SharedL2CacheHierarchy(
    l1d_size="64KiB", l1i_size="64KiB", l2_size="8MiB"
)

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Set the workload to Ubuntu 24.04 boot with systemd
# Use the standard obtain_resource, but handle potential download issues
print("Setting up Ubuntu 24.04 workload...")
try:
    workload = obtain_resource("x86-ubuntu-24.04-boot-with-systemd")
    print("Successfully obtained Ubuntu 24.04 workload")
except Exception as e:
    print(f"Warning: Resource download issue: {e}")
    print("This might be due to network issues or resource compatibility.")
    print("The simulation will continue and may use cached/local resources if available.")
    # Re-raise to let gem5 handle the resource management
    raise

# Set a custom command to run after boot
# This will automatically run the shm_rw_fs program
boot_commands = """
# Wait for system to fully boot
echo "Ubuntu FS mode booted successfully!"
echo "Setting up shm_rw test..."

# Create the shm_rw_fs binary from base64 encoded data
cat > /tmp/shm_rw_fs.b64 << 'EOF'
"""

# Read the binary file and convert to base64
import base64
try:
    with open("/shm-rw/shm_rw_fs", "rb") as f:
        binary_data = f.read()
        base64_data = base64.b64encode(binary_data).decode('ascii')
        
    # Split into chunks for the heredoc
    chunk_size = 76  # Standard base64 line length
    base64_chunks = [base64_data[i:i+chunk_size] for i in range(0, len(base64_data), chunk_size)]
    
    boot_commands += "\n".join(base64_chunks) + "\n"
    
except FileNotFoundError:
    print("WARNING: shm_rw_fs binary not found at /home/uuwyou/projects/shm-rw/shm_rw_fs")
    boot_commands += "# Binary not found - will need manual copy\n"

boot_commands += """EOF

# Decode and setup the binary
echo "Decoding binary..."
base64 -d /tmp/shm_rw_fs.b64 > /tmp/shm_rw_fs
chmod +x /tmp/shm_rw_fs

# Run the test
echo "Running shm_rw_fs test..."
cd /tmp
sudo /tmp/shm_rw_fs

echo "Test completed. System ready for interactive use."
/bin/bash
"""

workload.set_parameter("readfile_contents", boot_commands)
board.set_workload(workload)

# Create the simulator in FS mode
print("Creating FS mode simulator...")
simulator = Simulator(board=board)

print("Starting FS mode simulation...")
print("This will take considerable time to boot Ubuntu...")
print("=" * 60)
print("INSTRUCTIONS FOR RUNNING shm_rw:")
print("1. Wait for Ubuntu to fully boot (you'll see login prompt)")
print("2. The system will show instructions for running shm_rw")
print("3. You'll need to modify shm_rw to use proper memory access methods")
print("4. Consider using /dev/mem or ioremap() for physical memory access")
print("=" * 60)

# Run the simulation
simulator.run()

print("Simulation completed!")
