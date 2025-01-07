import struct

# Registers
reg3020 = 0x591A
reg3021 = 0x42E9

# Combine into 32-bit integer (little-endian)
combined = (reg3021 << 16) | reg3020

# Convert to float using IEEE 754 (little-endian)
float_value = struct.unpack('<f', combined.to_bytes(4, byteorder='little'))[0]

print(f"Combined value: {hex(combined)}")
print(f"Float value: {float_value}")
