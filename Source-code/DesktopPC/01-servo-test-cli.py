# -*- coding:utf-8 -*-
import binascii
import serial
import time
import argparse

def UARTServo(ser, servonum, angle):
    """
    Kontrol servo via UART dengan protokol: $[A-P][000-180]#
    
    Args:
        ser: Serial port object
        servonum: Nomor servo (1-16 untuk 16 channel controller)
        angle: Sudut servo (0-180)
    
    Protocol:
        Start: '$' (0x24)
        Servo: 'A'-'P' (0x41-0x50) untuk servo 1-16
        Angle: '000'-'180' (3 digit ASCII)
        End: '#' (0x23)
    
    Example: Servo 1 ke 180 derajat = "$A180#"
    """
    # Convert servo number to ASCII character (A-P)
    # Servo 1 = 'A' (65), Servo 2 = 'B' (66), ..., Servo 16 = 'P' (80)
    servo_char = 64 + servonum
    
    # Convert angle to 3-digit ASCII string
    date1 = int(angle/100 + 48)      # Hundreds digit
    date2 = int((angle%100)/10 + 48)  # Tens digit
    date3 = int(angle%10 + 48)        # Units digit
    
    # Build command: $ + ServoChar + Angle(3digits) + #
    cmd = bytearray([36, servo_char, date1, date2, date3, 35])
    
    # Debug output
    cmd_str = ''.join([chr(b) for b in cmd])
    print(f"  -> Mengirim: {cmd_str} (hex: {binascii.hexlify(cmd).decode()})")
    
    ser.write(cmd)
    time.sleep(0.05)

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description='Kontrol servo via UART - 16 Channel Servo Controller\nProtokol: $[A-P][000-180]# @ 9600bps 8N1',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Protokol komunikasi:
  Format: $[ServoChar][Angle]#
  - Start bit: '$' (ASCII 36 / 0x24)
  - Servo number: 'A'-'P' (ASCII 65-80) untuk servo 1-16
  - Servo angle: '000'-'180' (3 digit ASCII, range 0-180 derajat)
  - End bit: '#' (ASCII 35 / 0x23)
  
  Contoh: Servo 1 turn to 180 derajat = "$A180#"
  
  Serial: 9600bps, 8 data bits, No parity, 1 stop bit (8N1)

Contoh penggunaan:
  # Kontrol servo 1 ke sudut 90 derajat
  python script.py -s 1 -a 90
  
  # Kontrol servo 5 ke sudut 180 dengan custom port
  python script.py -s 5 -a 180 --port COM3
  
  # Kontrol servo 3 ke sudut 0
  python script.py -s 3 -a 0 -p COM4
  
  # Test 1 servo (sweep 0 -> 180)
  python script.py --test
  python script.py --test -s 5
  
  # Test semua servo ke posisi 90 derajat
  python script.py --test-all
  
  # Test sweep semua servo (0 -> 90 -> 180 -> 90 -> 0)
  python script.py --test-sweep
  
  # Set semua servo ke angle tertentu
  python script.py --all-angle 45
  
  # Reset semua servo ke posisi 90 (center)
  python script.py --reset
  
  # Default mode tanpa argument (test servo 1)
  python script.py

Catatan:
  - Servo number: 1-16 (16 channel controller)
  - Angle range: 0-180 (sudut standar servo)
  - Baudrate: 9600bps (fixed, tidak bisa diubah)
  - Di Windows gunakan: COM3, COM4, dll
  - Di Linux gunakan: /dev/ttyUSB0, /dev/ttyAMA0, dll
        '''
    )
    
    # Serial port argument
    parser.add_argument(
        '-p', '--port',
        type=str,
        default='COM23',
        help='Serial port (default: COM23). Windows: COM3, COM4. Linux: /dev/ttyUSB0'
    )
    
    # Servo control arguments
    parser.add_argument(
        '-s', '--servonum',
        type=int,
        default=None,
        help='Nomor servo (1-16 untuk 16 channel controller)'
    )
    
    parser.add_argument(
        '-a', '--angle',
        type=int,
        default=None,
        help='Sudut servo (0-180 derajat)'
    )
    
    # Test modes
    parser.add_argument(
        '--test',
        action='store_true',
        help='Mode test: gerakkan 1 servo dari 0 ke 180 derajat (gunakan -s untuk pilih servo)'
    )
    
    parser.add_argument(
        '--test-all',
        action='store_true',
        help='Test semua servo (1-16) ke posisi 90 derajat'
    )
    
    parser.add_argument(
        '--test-sweep',
        action='store_true',
        help='Test sweep semua servo: 0 -> 90 -> 180 -> 90 -> 0 derajat'
    )
    
    parser.add_argument(
        '--all-angle',
        type=int,
        default=None,
        help='Set semua servo (1-16) ke angle tertentu (0-180)'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset semua servo ke posisi center (90 derajat)'
    )
    
    args = parser.parse_args()
    
    # Validasi input untuk 16 channel controller
    if args.servonum is not None:
        if args.servonum < 1 or args.servonum > 16:
            parser.error("Servo number harus antara 1-16 (16 channel controller)")
    
    if args.angle is not None:
        if args.angle < 0 or args.angle > 180:
            parser.error("Angle harus antara 0-180 derajat")
    
    if args.all_angle is not None:
        if args.all_angle < 0 or args.all_angle > 180:
            parser.error("All-angle harus antara 0-180 derajat")
    
    # Configure serial port - Fixed 9600 8N1
    try:
        ser = serial.Serial(
            port=args.port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        print(f"OK Terhubung ke {args.port} @ 9600bps 8N1")
        print(f"  Protokol: $[A-P][000-180]#\n")
    except serial.SerialException as e:
        print(f"ERROR: Tidak bisa membuka port {args.port}")
        print(f"  Detail: {e}")
        print(f"\n  Tips:")
        print(f"  - Cek port tersedia di Device Manager (Windows)")
        print(f"  - Pastikan tidak ada program lain yang menggunakan port ini")
        print(f"  - Coba port lain: COM3, COM4, COM5, dll")
        return
    
    try:
        # Mode 1: Reset all servos to center
        if args.reset:
            print("=== RESET ALL SERVOS TO CENTER (90 derajat) ===")
            for i in range(1, 17):
                print(f"Servo {i} ('{chr(64+i)}') -> 90 derajat")
                UARTServo(ser, i, 90)
                time.sleep(0.1)
            print("\nOK Reset selesai! Semua servo di posisi center (90 derajat)")
        
        # Mode 2: Set all servos to specific angle
        elif args.all_angle is not None:
            print(f"=== SET ALL SERVOS TO {args.all_angle} DERAJAT ===")
            for i in range(1, 17):
                print(f"Servo {i} ('{chr(64+i)}') -> {args.all_angle} derajat")
                UARTServo(ser, i, args.all_angle)
                time.sleep(0.1)
            print(f"\nOK Semua servo di posisi {args.all_angle} derajat")
        
        # Mode 3: Test sweep all servos
        elif args.test_sweep:
            print("=== TEST SWEEP ALL SERVOS ===")
            positions = [0, 90, 180, 90, 0]
            
            for angle in positions:
                print(f"\n>>> Menggerakkan SEMUA servo ke {angle} derajat")
                for i in range(1, 17):
                    UARTServo(ser, i, angle)
                    time.sleep(0.05)
                print(f"OK Semua servo di posisi {angle} derajat")
                time.sleep(1.5)
            
            print("\nOK Test sweep selesai!")
        
        # Mode 4: Test all servos to 90 degrees
        elif args.test_all:
            print("=== TEST ALL SERVOS (1-16) ===")
            for i in range(1, 17):
                print(f"\nServo {i} ('{chr(64+i)}') -> 90 derajat")
                UARTServo(ser, i, 90)
                time.sleep(0.3)
            print("\nOK Test semua servo selesai!")
        
        # Mode 5: Test single servo (sweep 0 -> 180)
        elif args.test:
            servo = args.servonum if args.servonum else 1
            servo_char = chr(64 + servo)
            print(f"=== TEST MODE: Servo {servo} ('{servo_char}') ===\n")
            
            print(f"Menggerakkan servo {servo} ke posisi 0 derajat")
            UARTServo(ser, servo, 0)
            time.sleep(2)
            
            print(f"\nMenggerakkan servo {servo} ke posisi 180 derajat")
            UARTServo(ser, servo, 180)
            time.sleep(2)
            
            print("\nOK Test selesai!")
        
        # Mode 6: Single servo control
        elif args.servonum is not None and args.angle is not None:
            servo_char = chr(64 + args.servonum)
            print(f"Menggerakkan servo {args.servonum} ('{servo_char}') ke sudut {args.angle} derajat")
            UARTServo(ser, args.servonum, args.angle)
            print("OK Perintah terkirim")
        
        # Mode 7: Default test (backward compatibility)
        elif args.servonum is None and args.angle is None:
            print("=== DEFAULT TEST MODE: Servo 1 ('A') ===\n")
            
            print("Menggerakkan servo 1 ke posisi 0 derajat")
            UARTServo(ser, 1, 0)
            time.sleep(2)
            
            print("\nMenggerakkan servo 1 ke posisi 180 derajat")
            UARTServo(ser, 1, 180)
            time.sleep(2)
            
            print("\nOK Test selesai!")
        
        # Mode 8: Incomplete arguments
        else:
            parser.error("Gunakan --servonum DAN --angle bersamaan, atau gunakan salah satu mode test")
    
    except KeyboardInterrupt:
        print("\n\nProgram dihentikan oleh user (Ctrl+C)")
    except Exception as e:
        print(f"\nERROR: {e}")
    finally:
        ser.close()
        print("\nSerial port ditutup")

if __name__ == "__main__":
    main()
