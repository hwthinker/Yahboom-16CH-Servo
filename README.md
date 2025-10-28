# Yahboom 16 Channel Servo Controller

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Raspberry%20Pi-lightgrey.svg)

Program Python untuk mengontrol Yahboom 16 Channel Servo Controller via komunikasi serial UART dengan protokol `$[A-P][000-180]#`.

## 📋 Table of Contents

- [Spesifikasi](https://claude.ai/chat/73aa920a-fd71-4246-a4d2-2775e6f51ebc#-spesifikasi)
- [Protokol Komunikasi](https://claude.ai/chat/73aa920a-fd71-4246-a4d2-2775e6f51ebc#-protokol-komunikasi)
- [Instalasi](https://claude.ai/chat/73aa920a-fd71-4246-a4d2-2775e6f51ebc#-instalasi)
- [Penggunaan](https://claude.ai/chat/73aa920a-fd71-4246-a4d2-2775e6f51ebc#-penggunaan)
- [Mode Kontrol](https://claude.ai/chat/73aa920a-fd71-4246-a4d2-2775e6f51ebc#-mode-kontrol)
- [Contoh Penggunaan](https://claude.ai/chat/73aa920a-fd71-4246-a4d2-2775e6f51ebc#-contoh-penggunaan)
- [Parameter](https://claude.ai/chat/73aa920a-fd71-4246-a4d2-2775e6f51ebc#-parameter)
- [Hardware Connection](https://claude.ai/chat/73aa920a-fd71-4246-a4d2-2775e6f51ebc#-hardware-connection)
- [Troubleshooting](https://claude.ai/chat/73aa920a-fd71-4246-a4d2-2775e6f51ebc#-troubleshooting)
- [Debug Mode](https://claude.ai/chat/73aa920a-fd71-4246-a4d2-2775e6f51ebc#-debug-mode)
- [License](https://claude.ai/chat/73aa920a-fd71-4246-a4d2-2775e6f51ebc#-license)

## 🔧 Spesifikasi

| Item              | Spesifikasi                              |
| ----------------- | ---------------------------------------- |
| **Board**         | Yahboom 16 Channel Servo Controller      |
| **Protokol**      | `$[A-P][000-180]#`                       |
| **Baudrate**      | 9600 bps (fixed)                         |
| **Format Serial** | 8N1 (8 data bits, No parity, 1 stop bit) |
| **Channel**       | 16 servo (nomor 1-16)                    |
| **Range Sudut**   | 0-180 derajat                            |
| **Power Supply**  | 5-6V DC, 2-5A                            |

## 📡 Protokol Komunikasi

```
Format: $[ServoChar][Angle]#

┌─────────┬──────────────┬────────────┬─────────┐
│ Start   │ Servo Number │ Angle      │ End     │
├─────────┼──────────────┼────────────┼─────────┤
│ '$'     │ 'A' - 'P'    │ '000'-'180'│ '#'     │
│ 0x24    │ 0x41 - 0x50  │ 3 digits   │ 0x23    │
└─────────┴──────────────┴────────────┴─────────┘
```

**Mapping Servo:**

- Servo 1 = 'A' (ASCII 65)
- Servo 2 = 'B' (ASCII 66)
- ...
- Servo 16 = 'P' (ASCII 80)

**Contoh:**

- `$A180#` → Servo 1 ke 180°
- `$B090#` → Servo 2 ke 90°
- `$P000#` → Servo 16 ke 0°

## 🚀 Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/yahboom-servo-controller.git
cd yahboom-servo-controller
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

atau install langsung:

```bash
pip install pyserial
```

### 3. Setup Serial Port

#### Windows

1. Cek port di **Device Manager** → **Ports (COM & LPT)**
2. Catat nomor COM port (contoh: COM3, COM4)
3. Tidak perlu install driver tambahan

#### Linux / Raspberry Pi

```bash
# Cek port tersedia
ls /dev/tty*

# Tambahkan user ke grup dialout
sudo usermod -a -G dialout $USER

# Logout dan login lagi
```

**Raspberry Pi (tambahan):**

```bash
sudo raspi-config
# Pilih: Interface Options > Serial Port
# - Login shell over serial: No
# - Serial port hardware enabled: Yes
```

## 📖 Penggunaan

### Quick Start

```bash
# Default test (servo 1: 0° → 180°)
python script.py

# Kontrol servo 1 ke 90°
python script.py -s 1 -a 90

# Test semua servo
python script.py --test-all

# Help
python script.py --help
```

## 🎮 Mode Kontrol

### 1. Kontrol Single Servo

```bash
# Format: python script.py -s [servo] -a [angle]

python script.py -s 1 -a 90      # Servo 1 → 90°
python script.py -s 5 -a 180     # Servo 5 → 180°
python script.py -s 12 -a 0      # Servo 12 → 0°

# Dengan custom port
python script.py -s 3 -a 45 -p COM4              # Windows
python script.py -s 3 -a 45 -p /dev/ttyUSB0      # Linux
```

### 2. Test Mode - Single Servo

Test 1 servo dengan sweep dari 0° → 180°

```bash
python script.py --test          # Test servo 1 (default)
python script.py --test -s 5     # Test servo 5
python script.py --test -s 12    # Test servo 12
```

### 3. Test All - Semua Servo ke 90°

Test semua servo (1-16) satu per satu ke posisi 90°

```bash
python script.py --test-all
```

### 4. Test Sweep - Gerakan Bersamaan

Sweep semua servo bersamaan: **0° → 90° → 180° → 90° → 0°**

```bash
python script.py --test-sweep
```

### 5. Set All Angle - Posisi Custom

Set semua servo ke angle yang sama

```bash
python script.py --all-angle 45    # Semua servo → 45°
python script.py --all-angle 0     # Semua servo → 0°
python script.py --all-angle 180   # Semua servo → 180°
```

### 6. Reset - Ke Posisi Center

Reset semua servo ke posisi center (90°)

```bash
python script.py --reset
```

## 💡 Contoh Penggunaan

### Scenario 1: First Time Setup & Testing

```bash
# 1. Test koneksi dengan default test
python script.py

# 2. Reset semua servo ke center
python script.py --reset

# 3. Test sweep semua servo
python script.py --test-sweep

# 4. Test individual servo
python script.py --test -s 1
python script.py --test -s 8
```

### Scenario 2: Robot Arm Control

```bash
# Set posisi awal (semua ke 90°)
python script.py --reset

# Kontrol base rotation (servo 1)
python script.py -s 1 -a 45

# Kontrol shoulder (servo 2)
python script.py -s 2 -a 120

# Kontrol elbow (servo 3)
python script.py -s 3 -a 60

# Kontrol wrist (servo 4)
python script.py -s 4 -a 90

# Kontrol gripper (servo 5)
python script.py -s 5 -a 30
```

### Scenario 3: Hexapod Robot (6 Legs)

```bash
# Semua kaki ke posisi stand
python script.py --all-angle 90

# Kontrol Leg 1 (servo 1-3: coxa, femur, tibia)
python script.py -s 1 -a 45
python script.py -s 2 -a 90
python script.py -s 3 -a 135

# Kontrol Leg 2 (servo 4-6)
python script.py -s 4 -a 50
python script.py -s 5 -a 85
python script.py -s 6 -a 130
```

### Scenario 4: Humanoid Robot

```bash
# Reset posisi awal
python script.py --reset

# Right arm (servo 1-4)
python script.py -s 1 -a 90   # Shoulder
python script.py -s 2 -a 45   # Elbow
python script.py -s 3 -a 0    # Wrist rotation
python script.py -s 4 -a 30   # Gripper

# Left arm (servo 5-8)
python script.py -s 5 -a 90
python script.py -s 6 -a 135
python script.py -s 7 -a 180
python script.py -s 8 -a 60

# Head (servo 9-10)
python script.py -s 9 -a 90   # Pan
python script.py -s 10 -a 70  # Tilt
```

## 📊 Parameter

| Parameter      | Short | Type   | Default | Range | Deskripsi                         |
| -------------- | ----- | ------ | ------- | ----- | --------------------------------- |
| `--port`       | `-p`  | string | COM23   | -     | Serial port (COM3, /dev/ttyUSB0)  |
| `--servonum`   | `-s`  | int    | -       | 1-16  | Nomor servo                       |
| `--angle`      | `-a`  | int    | -       | 0-180 | Sudut servo (derajat)             |
| `--test`       | -     | flag   | -       | -     | Test 1 servo (0→180)              |
| `--test-all`   | -     | flag   | -       | -     | Test semua servo ke 90°           |
| `--test-sweep` | -     | flag   | -       | -     | Sweep semua servo (0→90→180→90→0) |
| `--all-angle`  | -     | int    | -       | 0-180 | Set semua servo ke angle tertentu |
| `--reset`      | -     | flag   | -       | -     | Reset semua servo ke 90°          |
| `--help`       | `-h`  | flag   | -       | -     | Tampilkan help                    |

## 🔌 Hardware Connection

### Pin Connection

```
┌─────────────────────────────────────────────────────────────┐
│  Yahboom Board          USB-to-Serial / Raspberry Pi        │
├─────────────────────────────────────────────────────────────┤
│  VCC        →          5-6V (external power supply)         │
│  GND        →          GND (common ground)                  │
│  RXD        →          TXD (dari USB-Serial/GPIO14)         │
│  TXD        →          RXD (optional, untuk feedback)       │
└─────────────────────────────────────────────────────────────┘
```

### Power Supply Recommendation

| Jumlah Servo | Arus Minimum | Power Supply |
| ------------ | ------------ | ------------ |
| 1-4 servo    | 2A           | 5V 2A        |
| 5-8 servo    | 3A           | 5V 3A        |
| 9-16 servo   | 5A+          | 5V 5A        |

**⚠️ PENTING:**

- **JANGAN** power servo dari USB komputer/Raspberry Pi
- Gunakan **power supply eksternal** 5-6V dengan arus cukup
- Sambungkan **GND bersama** antara board servo dan controller

### Wiring Diagram

```
        Computer/RaspberryPi              Yahboom Board
        ┌──────────────┐                  ┌──────────────┐
        │              │                  │              │
        │     USB      │──── USB Cable ───│  USB-Serial  │
        │              │                  │  Converter   │
        └──────────────┘                  │              │
                                          │  TXD ────────│──── RXD
                                          │  RXD ────────│──── TXD
                                          │  GND ────────│──── GND
                                          └──────────────┘
                                                  │
                                          ┌───────┴────────┐
                                          │  Power Supply  │
                                          │    5V 3A       │
                                          └────────────────┘
```

## 🐛 Troubleshooting

### ❌ Error: Port tidak bisa dibuka

**Windows:**

```
ERROR: Tidak bisa membuka port COM3
```

**Solusi:**

1. ✅ Cek Device Manager → Ports (COM & LPT)
2. ✅ Tutup program lain yang menggunakan port (Arduino IDE, PuTTY, Tera Term)
3. ✅ Coba port lain: COM4, COM5, dll
4. ✅ Cabut dan colok ulang USB cable
5. ✅ Restart komputer

**Linux:**

```
ERROR: Tidak bisa membuka port /dev/ttyUSB0
Permission denied
```

**Solusi:**

```bash
# 1. Cek user permission
groups $USER

# 2. Tambahkan ke grup dialout
sudo usermod -a -G dialout $USER

# 3. Logout dan login lagi, atau:
newgrp dialout

# 4. Cek port tersedia
ls -l /dev/ttyUSB*
ls -l /dev/ttyAMA*

# 5. Test permission (temporary fix)
sudo chmod 666 /dev/ttyUSB0
```

### ❌ Servo tidak bergerak

**Checklist:**

- ✅ Power supply sudah tersambung ke board (5-6V, minimal 2A)
- ✅ LED indicator di board menyala
- ✅ Servo sudah terpasang dengan benar ke channel
- ✅ Kabel servo tidak terbalik (signal, VCC, GND)
- ✅ Kabel serial (TX/RX) sudah benar
- ✅ GND bersama antara board dan controller
- ✅ Command yang dikirim sudah benar (cek output hex)

**Test:**

```bash
# Test dengan LED blink (jika ada LED di board)
python script.py --test-all

# Cek output hex di terminal
python script.py -s 1 -a 90
# Seharusnya muncul: -> Mengirim: $A090# (hex: 244130393023)
```

### ❌ Gerakan servo tidak smooth / patah-patah

**Penyebab:**

- Power supply kurang kuat
- Servo murah/rusak
- Delay terlalu cepat

**Solusi:** Edit file `script.py` di line ~40:

```python
time.sleep(0.05)  # Ubah jadi 0.1 atau 0.2 untuk gerakan lebih smooth
```

### ❌ Servo bergetar / jitter

**Penyebab:**

- Power supply tidak stabil
- Arus tidak cukup
- Kabel terlalu panjang

**Solusi:**

1. Gunakan power supply dengan kapasitor besar
2. Tambahkan kapasitor 1000µF di VCC/GND
3. Kurangi panjang kabel
4. Gunakan power supply dengan arus lebih besar

### ❌ Beberapa servo tidak bekerja

**Checklist:**

- ✅ Cek power supply (arus cukup untuk semua servo?)
- ✅ Test servo satu per satu: `python script.py --test -s 1`
- ✅ Cek koneksi kabel servo
- ✅ Cek channel di board (LED indicator)

## 🔍 Debug Mode

Program sudah include debug output yang menampilkan command yang dikirim:

```bash
$ python script.py -s 1 -a 90

OK Terhubung ke COM23 @ 9600bps 8N1
  Protokol: $[A-P][000-180]#

Menggerakkan servo 1 ('A') ke sudut 90 derajat
  -> Mengirim: $A090# (hex: 244130393023)
OK Perintah terkirim

Serial port ditutup
```

**Format Hex Breakdown:**

```
244130393023
│ ││││││││└─ 23 = '#'
│ │││││└└└─ 30 39 30 = '090' (angle)
│ │└└└─────── 41 = 'A' (servo 1)
└─└────────── 24 = '$'
```

## 📁 File Structure

```
yahboom-servo-controller/
├── script.py              # Main program
├── requirements.txt       # Python dependencies
├── README.md             # Documentation (this file)
├── LICENSE               # MIT License
└── examples/             # Example scripts (optional)
    ├── robot_arm.py
    ├── hexapod.py
    └── humanoid.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](https://claude.ai/chat/LICENSE) file for details.

## 🙏 Acknowledgments

- Yahboom untuk hardware 16 Channel Servo Controller
- PySerial library untuk komunikasi serial
- Python community

## 📚 Resources

- https://www.yahboom.net/study/16-servo-ctrl
- https://github.com/YahboomTechnology/16-channels-servo-debugging-board/tree/master

------

**Made with ❤️ for Robotics Community**

[![GitHub stars](https://img.shields.io/github/stars/yourusername/yahboom-servo-controller?style=social)](https://github.com/yourusername/yahboom-servo-controller/stargazers) [![GitHub forks](https://img.shields.io/github/forks/yourusername/yahboom-servo-controller?style=social)](https://github.com/yourusername/yahboom-servo-controller/network/members)