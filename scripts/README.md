# Scripts

This directory contains mainly Python scripts for reading data from a pulse oximeter (POX) and processing it.

## EXC and ALARM Fields Explanation

The `EXC` and `ALARM` fields are hexadecimal values representing binary-coded status flags indicating the state of the pulse oximeter. Each bit corresponds to a specific condition:

### EXC (Exception) Flags

| Bit | Hex  | Description           |
|------|-------|-----------------------|
| 1 (bit 0)  | 0x001 | No Sensor              |
| 2 (bit 1)  | 0x002 | Defective Sensor       |
| 3 (bit 2)  | 0x004 | Low Perfusion          |
| 4 (bit 3)  | 0x008 | Pulse Search           |
| 5 (bit 4)  | 0x010 | Interference           |
| 6 (bit 5)  | 0x020 | Sensor Off             |
| 7 (bit 6)  | 0x040 | Ambient Light          |
| 8 (bit 7)  | 0x080 | Unrecognized Sensor    |
| 11(bit 10) | 0x400 | Low Signal IQ          |
| 12(bit 11) | 0x800 | Masimo SET             |

### ALARM Flags

| Bit | Hex  | Description           |
|------|-------|-----------------------|
| 1 (bit 0)  | 0x001 | SPO₂ Above Threshold   |
| 2 (bit 1)  | 0x002 | SPO₂ Below Threshold   |
| 3 (bit 2)  | 0x004 | BPM Above Threshold    |
| 4 (bit 3)  | 0x008 | BPM Below Threshold    |
| 5 (bit 4)  | 0x010 | Alarm Raised           |
| 6 (bit 5)  | 0x020 | Alarm Muted            |
| 7 (bit 6)  | 0x040 | Low Battery            |

*Note:* Bit numbering starts at 0 for the least significant bit (LSB).
