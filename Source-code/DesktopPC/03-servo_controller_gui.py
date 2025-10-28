# -*- coding:utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import binascii
import time
import threading
import json
import math

class ServoControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("16 Channel Servo Controller + ARM Robot 6DOF")
        self.root.geometry("1200x800")
        
        # Serial connection
        self.ser = None
        self.connected = False
        
        # Servo states (1-16)
        self.servo_angles = {i: 90 for i in range(1, 17)}
        
        # ARM robot patterns
        self.patterns = {
            "Home Position": [90, 90, 90, 90, 90, 90],
            "Rest Position": [90, 45, 45, 90, 90, 90],
            "Reach Forward": [90, 60, 120, 90, 90, 45],
            "Reach Up": [90, 135, 45, 90, 90, 45],
            "Pick Position": [90, 60, 90, 120, 90, 90],
        }
        self.custom_patterns = {}
        
        # Animation state
        self.animating = False
        
        self.setup_ui()
        self.refresh_ports()
        
    def setup_ui(self):
        # ===== CONNECTION FRAME =====
        conn_frame = ttk.LabelFrame(self.root, text="Serial Connection", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=0, padx=5)
        self.port_combo = ttk.Combobox(conn_frame, width=15, state="readonly")
        self.port_combo.grid(row=0, column=1, padx=5)
        
        ttk.Button(conn_frame, text="Refresh", command=self.refresh_ports).grid(row=0, column=2, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=3, padx=5)
        
        self.status_label = ttk.Label(conn_frame, text="● Disconnected", foreground="red")
        self.status_label.grid(row=0, column=4, padx=10)
        
        # ===== MAIN NOTEBOOK =====
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Tab 1: Manual Control (16 Servos)
        self.setup_manual_tab()
        
        # Tab 2: ARM Robot Control (6 DOF)
        self.setup_arm_tab()
        
    def setup_manual_tab(self):
        manual_frame = ttk.Frame(self.notebook)
        self.notebook.add(manual_frame, text="Manual Control (16 Servos)")
        
        # Canvas with scrollbar
        canvas = tk.Canvas(manual_frame)
        scrollbar = ttk.Scrollbar(manual_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create 16 servo controls
        self.servo_controls = {}
        for i in range(1, 17):
            self.create_servo_control(scrollable_frame, i, (i-1)//4, (i-1)%4)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bottom control buttons
        bottom_frame = ttk.Frame(manual_frame)
        bottom_frame.pack(side="bottom", fill="x", pady=10)
        
        ttk.Button(bottom_frame, text="Reset All to 90°", 
                  command=self.reset_all_servos).pack(side="left", padx=5)
        ttk.Button(bottom_frame, text="Set All to 0°", 
                  command=lambda: self.set_all_servos(0)).pack(side="left", padx=5)
        ttk.Button(bottom_frame, text="Set All to 180°", 
                  command=lambda: self.set_all_servos(180)).pack(side="left", padx=5)
        
    def create_servo_control(self, parent, servo_num, row, col):
        frame = ttk.LabelFrame(parent, text=f"Servo {servo_num} ({chr(64+servo_num)})", padding=10)
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)
        
        # Angle display
        angle_var = tk.StringVar(value="90°")
        angle_label = ttk.Label(frame, textvariable=angle_var, font=("Arial", 16, "bold"))
        angle_label.pack()
        
        # Slider
        slider = ttk.Scale(frame, from_=0, to=180, orient="horizontal", length=200,
                          command=lambda v: self.on_slider_change(servo_num, v))
        slider.set(90)
        slider.pack(pady=5)
        
        # +/- buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="-10", width=5,
                  command=lambda: self.adjust_servo(servo_num, -10)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="-1", width=5,
                  command=lambda: self.adjust_servo(servo_num, -1)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="+1", width=5,
                  command=lambda: self.adjust_servo(servo_num, 1)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="+10", width=5,
                  command=lambda: self.adjust_servo(servo_num, 10)).pack(side="left", padx=2)
        
        # Center button
        center_frame = ttk.Frame(frame)
        center_frame.pack(pady=5)
        
        ttk.Button(center_frame, text="⊙ Center (90°)", 
                  command=lambda: self.center_servo(servo_num)).pack()
        
        # Entry for direct input
        entry_frame = ttk.Frame(frame)
        entry_frame.pack(pady=5)
        
        entry = ttk.Entry(entry_frame, width=8)
        entry.pack(side="left", padx=2)
        entry.bind("<Return>", lambda e: self.set_servo_from_entry(servo_num, entry))
        
        ttk.Button(entry_frame, text="Set", 
                  command=lambda: self.set_servo_from_entry(servo_num, entry)).pack(side="left")
        
        # Speed/Delay control
        speed_frame = ttk.Frame(frame)
        speed_frame.pack(pady=5)
        
        ttk.Label(speed_frame, text="Delay (ms):").pack(side="left", padx=2)
        speed_spinbox = ttk.Spinbox(speed_frame, from_=0, to=500, width=6, increment=10)
        speed_spinbox.set(50)
        speed_spinbox.pack(side="left", padx=2)
        
        self.servo_controls[servo_num] = {
            'slider': slider,
            'angle_var': angle_var,
            'entry': entry,
            'speed': speed_spinbox
        }
        
    def setup_arm_tab(self):
        arm_frame = ttk.Frame(self.notebook)
        self.notebook.add(arm_frame, text="ARM Robot 6DOF")
        
        # Left panel: Controls
        left_panel = ttk.Frame(arm_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Servo controls for ARM (Servo 1-6)
        controls_frame = ttk.LabelFrame(left_panel, text="Joint Controls", padding=10)
        controls_frame.pack(fill="both", expand=True)
        
        # Add info label
        info_label = ttk.Label(controls_frame, 
                              text="🤖 ARM Robot 6DOF - Joint Configuration",
                              font=("Arial", 11, "bold"),
                              foreground="navy")
        info_label.pack(pady=(0, 5))
        
        # Add SAFETY warning
        safety_frame = ttk.Frame(controls_frame)
        safety_frame.pack(fill="x", pady=(0, 10))
        
        safety_label = ttk.Label(safety_frame,
                                text="⚠️ SAFETY: S2 & S3 use higher delay (100ms) to prevent servo damage",
                                font=("Arial", 9),
                                foreground="red")
        safety_label.pack()
        
        self.arm_controls = {}
        joint_info = [
            ("Base", "S1", "Rotasi dasar robot (Yaw)"),
            ("Shoulder", "S2", "Gerakan bahu atas/bawah"),
            ("Elbow", "S3", "Gerakan siku/lengan bawah"),
            ("Wrist Pitch", "S4", "Pitch pergelangan tangan"),
            ("Wrist Roll", "S5", "Roll pergelangan tangan"),
            ("Gripper", "S6", "Buka/tutup gripper")
        ]
        
        for i in range(1, 7):
            self.create_arm_joint_control(controls_frame, i, joint_info[i-1], i-1)
        
        # Pattern controls
        pattern_frame = ttk.LabelFrame(left_panel, text="Movement Patterns", padding=10)
        pattern_frame.pack(fill="x", pady=10)
        
        # Pattern list
        list_frame = ttk.Frame(pattern_frame)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.pattern_listbox = tk.Listbox(list_frame, height=8, yscrollcommand=scrollbar.set)
        self.pattern_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.pattern_listbox.yview)
        
        self.refresh_pattern_list()
        
        # Pattern buttons
        btn_frame = ttk.Frame(pattern_frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="Apply Pattern", 
                  command=self.apply_pattern).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Save Current as Pattern", 
                  command=self.save_current_pattern).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Delete Pattern", 
                  command=self.delete_pattern).pack(side="left", padx=2)
        
        # Animation controls
        anim_frame = ttk.LabelFrame(pattern_frame, text="Animation", padding=5)
        anim_frame.pack(fill="x", pady=5)
        
        ttk.Label(anim_frame, text="Speed (ms):").pack(side="left", padx=5)
        self.anim_speed = ttk.Spinbox(anim_frame, from_=10, to=1000, width=8)
        self.anim_speed.set(50)
        self.anim_speed.pack(side="left", padx=5)
        
        self.animate_btn = ttk.Button(anim_frame, text="Animate to Pattern", 
                                     command=self.animate_to_pattern)
        self.animate_btn.pack(side="left", padx=5)
        
        # Pattern file operations
        file_frame = ttk.Frame(pattern_frame)
        file_frame.pack(fill="x", pady=5)
        
        ttk.Button(file_frame, text="Load Patterns", 
                  command=self.load_patterns_file).pack(side="left", padx=2)
        ttk.Button(file_frame, text="Save Patterns", 
                  command=self.save_patterns_file).pack(side="left", padx=2)
        
        # Right panel: 3D Visualization
        right_panel = ttk.LabelFrame(arm_frame, text="ARM Visualization", padding=10)
        right_panel.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        self.arm_canvas = tk.Canvas(right_panel, width=400, height=600, bg="white")
        self.arm_canvas.pack()
        
        self.draw_arm()
        
    def create_arm_joint_control(self, parent, servo_num, joint_info, row):
        joint_name, servo_label, description = joint_info
        
        # Main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="x", pady=8)
        
        # Header with servo info
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x")
        
        # Joint name and servo label
        label_text = f"{joint_name} ({servo_label})"
        label = ttk.Label(header_frame, text=label_text, width=18, 
                         font=("Arial", 10, "bold"))
        label.pack(side="left", padx=5)
        
        # Description
        desc_label = ttk.Label(header_frame, text=f"- {description}", 
                              font=("Arial", 9), foreground="gray")
        desc_label.pack(side="left", padx=5)
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=2)
        
        # Spacing
        ttk.Label(control_frame, text="", width=3).pack(side="left")
        
        # Angle display
        angle_var = tk.StringVar(value="90°")
        angle_label = ttk.Label(control_frame, textvariable=angle_var, width=6, 
                               font=("Arial", 10, "bold"), foreground="blue")
        angle_label.pack(side="left", padx=5)
        
        # Slider
        slider = ttk.Scale(control_frame, from_=0, to=180, orient="horizontal", length=200,
                          command=lambda v: self.on_arm_slider_change(servo_num, v))
        slider.set(90)
        slider.pack(side="left", padx=5)
        
        # +/- buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side="left", padx=5)
        
        ttk.Button(btn_frame, text="-5", width=4,
                  command=lambda: self.adjust_arm_servo(servo_num, -5)).pack(side="left", padx=1)
        ttk.Button(btn_frame, text="+5", width=4,
                  command=lambda: self.adjust_arm_servo(servo_num, 5)).pack(side="left", padx=1)
        
        # Center button
        ttk.Button(control_frame, text="⊙", width=3,
                  command=lambda: self.center_arm_servo(servo_num)).pack(side="left", padx=2)
        
        # Delay control (NEW!)
        delay_frame = ttk.Frame(control_frame)
        delay_frame.pack(side="left", padx=5)
        
        ttk.Label(delay_frame, text="Delay:", font=("Arial", 8)).pack(side="left", padx=2)
        delay_spinbox = ttk.Spinbox(delay_frame, from_=0, to=500, width=5, increment=10)
        
        # Set default delays based on joint load
        # S2 & S3 (shoulder & elbow) need slower defaults for safety
        if servo_num in [2, 3]:  # Shoulder and Elbow - heavy load
            delay_spinbox.set(100)  # Slower default for safety
        elif servo_num == 1:  # Base - medium load
            delay_spinbox.set(50)
        else:  # S4, S5, S6 - lighter load
            delay_spinbox.set(30)
            
        delay_spinbox.pack(side="left")
        ttk.Label(delay_frame, text="ms", font=("Arial", 8)).pack(side="left", padx=2)
        
        # Separator line
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=2)
        
        self.arm_controls[servo_num] = {
            'slider': slider,
            'angle_var': angle_var,
            'delay': delay_spinbox  # Store delay control
        }
        
    def on_slider_change(self, servo_num, value):
        angle = int(float(value))
        self.servo_angles[servo_num] = angle
        self.servo_controls[servo_num]['angle_var'].set(f"{angle}°")
        self.send_servo_command(servo_num, angle)
        
    def on_arm_slider_change(self, servo_num, value):
        angle = int(float(value))
        self.servo_angles[servo_num] = angle
        self.arm_controls[servo_num]['angle_var'].set(f"{angle}°")
        
        # Get delay from ARM control (use arm delay, not manual control delay)
        try:
            delay = int(self.arm_controls[servo_num]['delay'].get())
            time.sleep(delay / 1000.0)
        except:
            time.sleep(0.05)  # Default fallback
            
        self.send_servo_command(servo_num, angle)
        self.draw_arm()
        
    def adjust_servo(self, servo_num, delta):
        current = self.servo_angles[servo_num]
        new_angle = max(0, min(180, current + delta))
        self.servo_controls[servo_num]['slider'].set(new_angle)
        
    def center_servo(self, servo_num):
        """Set servo to center position (90 degrees)"""
        self.servo_controls[servo_num]['slider'].set(90)
        
    def adjust_arm_servo(self, servo_num, delta):
        current = self.servo_angles[servo_num]
        new_angle = max(0, min(180, current + delta))
        self.arm_controls[servo_num]['slider'].set(new_angle)
        
    def center_arm_servo(self, servo_num):
        """Set ARM servo to center position (90 degrees)"""
        self.arm_controls[servo_num]['slider'].set(90)
        
    def set_servo_from_entry(self, servo_num, entry):
        try:
            angle = int(entry.get())
            if 0 <= angle <= 180:
                self.servo_controls[servo_num]['slider'].set(angle)
                entry.delete(0, tk.END)
            else:
                messagebox.showwarning("Invalid Input", "Angle must be between 0 and 180")
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid number")
            
    def send_servo_command(self, servo_num, angle):
        if not self.connected or self.ser is None:
            return
            
        try:
            # Protocol: $[A-P][000-180]#
            servo_char = 64 + servo_num
            date1 = int(angle/100 + 48)
            date2 = int((angle%100)/10 + 48)
            date3 = int(angle%10 + 48)
            
            cmd = bytearray([36, servo_char, date1, date2, date3, 35])
            self.ser.write(cmd)
            
            # Get delay from servo control if available
            if servo_num in self.servo_controls:
                try:
                    delay = int(self.servo_controls[servo_num]['speed'].get())
                    time.sleep(delay / 1000.0)
                except:
                    time.sleep(0.01)
            else:
                time.sleep(0.01)
        except Exception as e:
            messagebox.showerror("Communication Error", f"Failed to send command: {e}")
            
    def reset_all_servos(self):
        for i in range(1, 17):
            self.servo_controls[i]['slider'].set(90)
            
    def set_all_servos(self, angle):
        for i in range(1, 17):
            self.servo_controls[i]['slider'].set(angle)
            
    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)
            
    def toggle_connection(self):
        if not self.connected:
            self.connect()
        else:
            self.disconnect()
            
    def connect(self):
        port = self.port_combo.get()
        if not port:
            messagebox.showwarning("No Port", "Please select a port")
            return
            
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.connected = True
            self.connect_btn.config(text="Disconnect")
            self.status_label.config(text="● Connected", foreground="green")
            messagebox.showinfo("Connected", f"Connected to {port} @ 9600bps")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            
    def disconnect(self):
        if self.ser:
            self.ser.close()
        self.connected = False
        self.connect_btn.config(text="Connect")
        self.status_label.config(text="● Disconnected", foreground="red")
        
    def refresh_pattern_list(self):
        self.pattern_listbox.delete(0, tk.END)
        
        # Add built-in patterns
        for name in self.patterns.keys():
            self.pattern_listbox.insert(tk.END, f"[Built-in] {name}")
            
        # Add custom patterns
        for name in self.custom_patterns.keys():
            self.pattern_listbox.insert(tk.END, f"[Custom] {name}")
            
    def apply_pattern(self):
        selection = self.pattern_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a pattern")
            return
            
        item = self.pattern_listbox.get(selection[0])
        pattern_name = item.replace("[Built-in] ", "").replace("[Custom] ", "")
        
        # Get pattern angles
        if pattern_name in self.patterns:
            angles = self.patterns[pattern_name]
        elif pattern_name in self.custom_patterns:
            angles = self.custom_patterns[pattern_name]
        else:
            return
            
        # Apply to servos 1-6
        for i, angle in enumerate(angles, start=1):
            self.arm_controls[i]['slider'].set(angle)
            
    def animate_to_pattern(self):
        selection = self.pattern_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a pattern")
            return
            
        if self.animating:
            messagebox.showinfo("Busy", "Animation already in progress")
            return
            
        item = self.pattern_listbox.get(selection[0])
        pattern_name = item.replace("[Built-in] ", "").replace("[Custom] ", "")
        
        # Get pattern angles
        if pattern_name in self.patterns:
            target_angles = self.patterns[pattern_name]
        elif pattern_name in self.custom_patterns:
            target_angles = self.custom_patterns[pattern_name]
        else:
            return
            
        # Start animation in separate thread
        self.animating = True
        self.animate_btn.config(state="disabled")
        
        thread = threading.Thread(target=self._animate_thread, args=(target_angles,))
        thread.daemon = True
        thread.start()
        
    def _animate_thread(self, target_angles):
        try:
            speed = int(self.anim_speed.get())
            current_angles = [self.servo_angles[i] for i in range(1, 7)]
            
            # Calculate steps (10 steps for smooth animation)
            steps = 20
            
            for step in range(steps + 1):
                for i in range(6):
                    servo_num = i + 1
                    start = current_angles[i]
                    end = target_angles[i]
                    angle = int(start + (end - start) * step / steps)
                    
                    # Update UI from main thread
                    self.root.after(0, lambda s=servo_num, a=angle: 
                                   self.arm_controls[s]['slider'].set(a))
                    
                time.sleep(speed / 1000.0)
                
        finally:
            self.animating = False
            self.root.after(0, lambda: self.animate_btn.config(state="normal"))
            
    def save_current_pattern(self):
        # Get current angles for servos 1-6
        current = [self.servo_angles[i] for i in range(1, 7)]
        
        # Ask for pattern name
        dialog = tk.Toplevel(self.root)
        dialog.title("Save Pattern")
        dialog.geometry("300x100")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Pattern Name:").pack(pady=10)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Invalid Name", "Please enter a pattern name")
                return
            if name in self.patterns:
                messagebox.showwarning("Invalid Name", "Cannot overwrite built-in patterns")
                return
                
            self.custom_patterns[name] = current
            self.refresh_pattern_list()
            dialog.destroy()
            messagebox.showinfo("Saved", f"Pattern '{name}' saved successfully")
            
        ttk.Button(dialog, text="Save", command=save).pack(pady=5)
        
    def delete_pattern(self):
        selection = self.pattern_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a pattern")
            return
            
        item = self.pattern_listbox.get(selection[0])
        
        if "[Built-in]" in item:
            messagebox.showwarning("Cannot Delete", "Cannot delete built-in patterns")
            return
            
        pattern_name = item.replace("[Custom] ", "")
        
        if messagebox.askyesno("Confirm Delete", f"Delete pattern '{pattern_name}'?"):
            del self.custom_patterns[pattern_name]
            self.refresh_pattern_list()
            
    def save_patterns_file(self):
        if not self.custom_patterns:
            messagebox.showinfo("No Patterns", "No custom patterns to save")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.custom_patterns, f, indent=2)
                messagebox.showinfo("Saved", f"Patterns saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
                
    def load_patterns_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    loaded = json.load(f)
                self.custom_patterns.update(loaded)
                self.refresh_pattern_list()
                messagebox.showinfo("Loaded", f"Loaded {len(loaded)} patterns")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")
                
    def draw_arm(self):
        """Draw simplified 2D representation of 6DOF robot arm"""
        self.arm_canvas.delete("all")
        
        # Get current angles for servos 1-6
        base = self.servo_angles[1]
        shoulder = self.servo_angles[2]
        elbow = self.servo_angles[3]
        wrist_pitch = self.servo_angles[4]
        wrist_roll = self.servo_angles[5]
        gripper = self.servo_angles[6]
        
        # Canvas center
        cx, cy = 200, 500
        
        # Link lengths (pixels)
        base_height = 50
        upper_arm = 150
        forearm = 120
        wrist = 60
        
        # Convert angles to radians (adjust for servo orientation)
        shoulder_rad = math.radians(180 - shoulder)
        elbow_rad = math.radians(180 - elbow)
        wrist_rad = math.radians(180 - wrist_pitch)
        
        # Calculate positions
        # Base (just rotation, shown as circle)
        base_x = cx
        base_y = cy
        
        # Shoulder joint
        shoulder_x = base_x
        shoulder_y = base_y - base_height
        
        # Elbow joint
        elbow_x = shoulder_x + upper_arm * math.cos(shoulder_rad)
        elbow_y = shoulder_y - upper_arm * math.sin(shoulder_rad)
        
        # Wrist joint
        forearm_angle = shoulder_rad + elbow_rad - math.pi
        wrist_x = elbow_x + forearm * math.cos(forearm_angle)
        wrist_y = elbow_y - forearm * math.sin(forearm_angle)
        
        # End effector
        wrist_angle = forearm_angle + wrist_rad - math.pi
        end_x = wrist_x + wrist * math.cos(wrist_angle)
        end_y = wrist_y - wrist * math.sin(wrist_angle)
        
        # Draw ground
        self.arm_canvas.create_line(0, cy + 20, 400, cy + 20, fill="gray", width=3)
        
        # Draw base
        self.arm_canvas.create_oval(base_x - 30, base_y - 10, base_x + 30, base_y + 30, 
                                    fill="lightgray", outline="black", width=2)
        self.arm_canvas.create_text(base_x, base_y + 50, text=f"Base: {base}°", font=("Arial", 9))
        
        # Draw links
        # Base to shoulder
        self.arm_canvas.create_line(base_x, base_y, shoulder_x, shoulder_y, 
                                    fill="blue", width=8)
        
        # Upper arm
        self.arm_canvas.create_line(shoulder_x, shoulder_y, elbow_x, elbow_y, 
                                    fill="green", width=8)
        
        # Forearm
        self.arm_canvas.create_line(elbow_x, elbow_y, wrist_x, wrist_y, 
                                    fill="orange", width=8)
        
        # Wrist to end effector
        self.arm_canvas.create_line(wrist_x, wrist_y, end_x, end_y, 
                                    fill="red", width=6)
        
        # Draw joints
        joint_radius = 8
        self.arm_canvas.create_oval(shoulder_x - joint_radius, shoulder_y - joint_radius,
                                    shoulder_x + joint_radius, shoulder_y + joint_radius,
                                    fill="darkblue", outline="black", width=2)
        
        self.arm_canvas.create_oval(elbow_x - joint_radius, elbow_y - joint_radius,
                                    elbow_x + joint_radius, elbow_y + joint_radius,
                                    fill="darkgreen", outline="black", width=2)
        
        self.arm_canvas.create_oval(wrist_x - joint_radius, wrist_y - joint_radius,
                                    wrist_x + joint_radius, wrist_y + joint_radius,
                                    fill="darkorange", outline="black", width=2)
        
        # Draw gripper
        gripper_open = (180 - gripper) / 180.0 * 20
        self.arm_canvas.create_line(end_x - gripper_open, end_y - 10,
                                    end_x - gripper_open, end_y + 10,
                                    fill="purple", width=4)
        self.arm_canvas.create_line(end_x + gripper_open, end_y - 10,
                                    end_x + gripper_open, end_y + 10,
                                    fill="purple", width=4)
        
        # Labels
        self.arm_canvas.create_text(shoulder_x + 20, shoulder_y - 20, 
                                    text=f"S: {shoulder}°", font=("Arial", 8))
        self.arm_canvas.create_text(elbow_x + 20, elbow_y - 20, 
                                    text=f"E: {elbow}°", font=("Arial", 8))
        self.arm_canvas.create_text(wrist_x + 20, wrist_y - 20, 
                                    text=f"W: {wrist_pitch}°", font=("Arial", 8))
        self.arm_canvas.create_text(end_x, end_y + 30, 
                                    text=f"G: {gripper}°", font=("Arial", 8))
        
        # Info text
        self.arm_canvas.create_text(200, 30, 
                                    text="6DOF Robot ARM Visualization", 
                                    font=("Arial", 14, "bold"))
        self.arm_canvas.create_text(200, 50, 
                                    text="(Side View - 2D Projection)", 
                                    font=("Arial", 10))

def main():
    root = tk.Tk()
    app = ServoControllerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
