# -*- coding:utf-8 -*-
"""
Demo Mode untuk Servo Controller GUI
Berjalan tanpa koneksi serial hardware untuk testing dan demonstrasi
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import threading
import json
import math

class ServoControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("16 Channel Servo Controller + ARM Robot 6DOF [DEMO MODE]")
        self.root.geometry("1200x800")
        
        # Demo mode - no serial
        self.ser = None
        self.connected = True  # Always "connected" in demo mode
        
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
        
        # Demo mode banner
        banner = ttk.Frame(self.root)
        banner.pack(fill="x", padx=10, pady=5)
        ttk.Label(banner, text="🎮 DEMO MODE - Running without serial hardware", 
                 font=("Arial", 12, "bold"), foreground="blue").pack()
        
        self.setup_ui()
        
        # Load example patterns
        self.load_example_patterns()
        
    def load_example_patterns(self):
        """Load example patterns from file if available"""
        try:
            with open('example_patterns.json', 'r') as f:
                self.custom_patterns = json.load(f)
            self.refresh_pattern_list()
            print("✓ Example patterns loaded")
        except FileNotFoundError:
            print("ℹ No example_patterns.json found, using built-in patterns only")
        
    def setup_ui(self):
        # ===== CONNECTION FRAME (DEMO) =====
        conn_frame = ttk.LabelFrame(self.root, text="Demo Mode Status", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ttk.Label(conn_frame, text="● Demo Mode Active (No Hardware Required)", 
                                      foreground="green", font=("Arial", 10, "bold"))
        self.status_label.pack()
        
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
        
        self.pattern_listbox = tk.Listbox(list_frame, height=10, yscrollcommand=scrollbar.set)
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
        
        # Quick demo button
        ttk.Button(anim_frame, text="🎬 Demo Sequence", 
                  command=self.run_demo_sequence,
                  style="Accent.TButton").pack(side="left", padx=5)
        
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
        
        # Delay control (NEW! SAFETY FEATURE)
        delay_frame = ttk.Frame(control_frame)
        delay_frame.pack(side="left", padx=5)
        
        ttk.Label(delay_frame, text="Delay:", font=("Arial", 8)).pack(side="left", padx=2)
        delay_spinbox = ttk.Spinbox(delay_frame, from_=0, to=500, width=5, increment=10)
        
        # Set default delays based on joint load - IMPORTANT FOR SAFETY!
        # S2 & S3 (shoulder & elbow) need slower defaults to prevent damage
        if servo_num in [2, 3]:  # Shoulder and Elbow - heavy load, SLOWER
            delay_spinbox.set(100)  # 100ms default for safety
        elif servo_num == 1:  # Base - medium load
            delay_spinbox.set(50)
        else:  # S4, S5, S6 - lighter load, can be faster
            delay_spinbox.set(30)
            
        delay_spinbox.pack(side="left")
        ttk.Label(delay_frame, text="ms", font=("Arial", 8)).pack(side="left", padx=2)
        
        # Separator line
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=2)
        
        self.arm_controls[servo_num] = {
            'slider': slider,
            'angle_var': angle_var,
            'delay': delay_spinbox  # Store delay control for safety
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
        
        # Get delay from ARM control for safety
        try:
            delay = int(self.arm_controls[servo_num]['delay'].get())
            if delay > 0:
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
        # Demo mode - just print
        servo_char = chr(64 + servo_num)
        print(f"📡 DEMO: Servo {servo_num} ({servo_char}) -> {angle}° | Command: ${servo_char}{angle:03d}#")
        
        # Apply delay if in servo_controls
        if servo_num in self.servo_controls:
            try:
                delay = int(self.servo_controls[servo_num]['speed'].get())
                if delay > 0:
                    time.sleep(delay / 1000.0)
            except:
                pass
            
    def reset_all_servos(self):
        for i in range(1, 17):
            self.servo_controls[i]['slider'].set(90)
        print("🔄 DEMO: All servos reset to 90°")
            
    def set_all_servos(self, angle):
        for i in range(1, 17):
            self.servo_controls[i]['slider'].set(angle)
        print(f"🔄 DEMO: All servos set to {angle}°")
            
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
            
        print(f"✓ DEMO: Pattern '{pattern_name}' applied: {angles}")
            
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
            
        print(f"🎬 DEMO: Animating to pattern '{pattern_name}'...")
            
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
            
            # Calculate steps (20 steps for smooth animation)
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
                
            print("✓ DEMO: Animation complete!")
                
        finally:
            self.animating = False
            self.root.after(0, lambda: self.animate_btn.config(state="normal"))
            
    def run_demo_sequence(self):
        """Run a demo sequence through multiple patterns"""
        if self.animating:
            messagebox.showinfo("Busy", "Animation already in progress")
            return
            
        print("\n🎬 Starting demo sequence...")
        
        sequence = [
            "Home Position",
            "Reach Forward",
            "Pick Position",
            "Reach Up",
            "Rest Position",
            "Home Position"
        ]
        
        self.animating = True
        self.animate_btn.config(state="disabled")
        
        def run_sequence():
            try:
                speed = int(self.anim_speed.get())
                
                for pattern_name in sequence:
                    print(f"  → Moving to: {pattern_name}")
                    
                    if pattern_name in self.patterns:
                        target_angles = self.patterns[pattern_name]
                    elif pattern_name in self.custom_patterns:
                        target_angles = self.custom_patterns[pattern_name]
                    else:
                        continue
                        
                    current_angles = [self.servo_angles[i] for i in range(1, 7)]
                    steps = 20
                    
                    for step in range(steps + 1):
                        for i in range(6):
                            servo_num = i + 1
                            start = current_angles[i]
                            end = target_angles[i]
                            angle = int(start + (end - start) * step / steps)
                            
                            self.root.after(0, lambda s=servo_num, a=angle: 
                                           self.arm_controls[s]['slider'].set(a))
                        
                        time.sleep(speed / 1000.0)
                    
                    # Hold position
                    time.sleep(1.0)
                
                print("✓ Demo sequence complete!\n")
                    
            finally:
                self.animating = False
                self.root.after(0, lambda: self.animate_btn.config(state="normal"))
        
        thread = threading.Thread(target=run_sequence)
        thread.daemon = True
        thread.start()
            
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
            print(f"💾 DEMO: Pattern '{name}' saved: {current}")
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
            print(f"🗑️ DEMO: Pattern '{pattern_name}' deleted")
            
    def save_patterns_file(self):
        if not self.custom_patterns:
            messagebox.showinfo("No Patterns", "No custom patterns to save")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="my_patterns.json"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.custom_patterns, f, indent=2)
                print(f"💾 DEMO: Patterns saved to {filename}")
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
                print(f"📂 DEMO: Loaded {len(loaded)} patterns from {filename}")
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
        base_x = cx
        base_y = cy
        
        shoulder_x = base_x
        shoulder_y = base_y - base_height
        
        elbow_x = shoulder_x + upper_arm * math.cos(shoulder_rad)
        elbow_y = shoulder_y - upper_arm * math.sin(shoulder_rad)
        
        forearm_angle = shoulder_rad + elbow_rad - math.pi
        wrist_x = elbow_x + forearm * math.cos(forearm_angle)
        wrist_y = elbow_y - forearm * math.sin(forearm_angle)
        
        wrist_angle = forearm_angle + wrist_rad - math.pi
        end_x = wrist_x + wrist * math.cos(wrist_angle)
        end_y = wrist_y - wrist * math.sin(wrist_angle)
        
        # Draw ground
        self.arm_canvas.create_line(0, cy + 20, 400, cy + 20, fill="gray", width=3)
        self.arm_canvas.create_rectangle(0, cy + 20, 400, 600, fill="#f0f0f0", outline="")
        
        # Draw shadow (simple)
        shadow_offset = 5
        self.arm_canvas.create_line(base_x + shadow_offset, base_y + shadow_offset, 
                                    shoulder_x + shadow_offset, shoulder_y + shadow_offset, 
                                    fill="lightgray", width=6)
        self.arm_canvas.create_line(shoulder_x + shadow_offset, shoulder_y + shadow_offset, 
                                    elbow_x + shadow_offset, elbow_y + shadow_offset, 
                                    fill="lightgray", width=6)
        
        # Draw base
        self.arm_canvas.create_oval(base_x - 30, base_y - 10, base_x + 30, base_y + 30, 
                                    fill="lightgray", outline="black", width=2)
        self.arm_canvas.create_arc(base_x - 25, base_y - 5, base_x + 25, base_y + 25,
                                   start=0, extent=180, fill="darkgray", outline="")
        self.arm_canvas.create_text(base_x, base_y + 50, text=f"Base: {base}°", 
                                    font=("Arial", 9, "bold"))
        
        # Draw links with gradient effect
        # Base to shoulder
        self.arm_canvas.create_line(base_x, base_y, shoulder_x, shoulder_y, 
                                    fill="navy", width=10)
        self.arm_canvas.create_line(base_x, base_y, shoulder_x, shoulder_y, 
                                    fill="blue", width=8)
        
        # Upper arm
        self.arm_canvas.create_line(shoulder_x, shoulder_y, elbow_x, elbow_y, 
                                    fill="darkgreen", width=10)
        self.arm_canvas.create_line(shoulder_x, shoulder_y, elbow_x, elbow_y, 
                                    fill="green", width=8)
        
        # Forearm
        self.arm_canvas.create_line(elbow_x, elbow_y, wrist_x, wrist_y, 
                                    fill="darkorange", width=10)
        self.arm_canvas.create_line(elbow_x, elbow_y, wrist_x, wrist_y, 
                                    fill="orange", width=8)
        
        # Wrist to end effector
        self.arm_canvas.create_line(wrist_x, wrist_y, end_x, end_y, 
                                    fill="darkred", width=8)
        self.arm_canvas.create_line(wrist_x, wrist_y, end_x, end_y, 
                                    fill="red", width=6)
        
        # Draw joints with 3D effect
        joint_radius = 10
        
        # Shoulder
        self.arm_canvas.create_oval(shoulder_x - joint_radius, shoulder_y - joint_radius,
                                    shoulder_x + joint_radius, shoulder_y + joint_radius,
                                    fill="navy", outline="black", width=2)
        self.arm_canvas.create_oval(shoulder_x - joint_radius + 2, shoulder_y - joint_radius + 2,
                                    shoulder_x + joint_radius - 2, shoulder_y + joint_radius - 2,
                                    fill="darkblue", outline="")
        
        # Elbow
        self.arm_canvas.create_oval(elbow_x - joint_radius, elbow_y - joint_radius,
                                    elbow_x + joint_radius, elbow_y + joint_radius,
                                    fill="darkgreen", outline="black", width=2)
        self.arm_canvas.create_oval(elbow_x - joint_radius + 2, elbow_y - joint_radius + 2,
                                    elbow_x + joint_radius - 2, elbow_y + joint_radius - 2,
                                    fill="green", outline="")
        
        # Wrist
        self.arm_canvas.create_oval(wrist_x - joint_radius, wrist_y - joint_radius,
                                    wrist_x + joint_radius, wrist_y + joint_radius,
                                    fill="darkorange", outline="black", width=2)
        self.arm_canvas.create_oval(wrist_x - joint_radius + 2, wrist_y - joint_radius + 2,
                                    wrist_x + joint_radius - 2, wrist_y + joint_radius - 2,
                                    fill="orange", outline="")
        
        # Draw gripper with more detail
        gripper_open = (180 - gripper) / 180.0 * 20
        
        # Gripper fingers
        self.arm_canvas.create_rectangle(end_x - gripper_open - 3, end_y - 15,
                                        end_x - gripper_open + 3, end_y + 15,
                                        fill="purple", outline="black", width=2)
        self.arm_canvas.create_rectangle(end_x + gripper_open - 3, end_y - 15,
                                        end_x + gripper_open + 3, end_y + 15,
                                        fill="purple", outline="black", width=2)
        
        # Gripper base
        self.arm_canvas.create_oval(end_x - 8, end_y - 8,
                                    end_x + 8, end_y + 8,
                                    fill="darkviolet", outline="black", width=2)
        
        # Labels with background
        labels = [
            (shoulder_x + 25, shoulder_y - 25, f"Shoulder\n{shoulder}°"),
            (elbow_x + 25, elbow_y - 25, f"Elbow\n{elbow}°"),
            (wrist_x + 25, wrist_y - 25, f"Wrist\n{wrist_pitch}°"),
            (end_x, end_y + 35, f"Gripper: {gripper}°")
        ]
        
        for x, y, text in labels:
            # Background
            self.arm_canvas.create_rectangle(x - 25, y - 12, x + 25, y + 12,
                                            fill="lightyellow", outline="black")
            # Text
            self.arm_canvas.create_text(x, y, text=text, font=("Arial", 8, "bold"))
        
        # Info text with background
        self.arm_canvas.create_rectangle(0, 0, 400, 70, fill="lightblue", outline="")
        self.arm_canvas.create_text(200, 20, 
                                    text="6DOF Robot ARM Visualization", 
                                    font=("Arial", 14, "bold"))
        self.arm_canvas.create_text(200, 40, 
                                    text="Side View - 2D Projection", 
                                    font=("Arial", 10))
        self.arm_canvas.create_text(200, 55, 
                                    text="🎮 DEMO MODE", 
                                    font=("Arial", 9), fill="blue")

def main():
    root = tk.Tk()
    app = ServoControllerGUI(root)
    
    print("\n" + "="*60)
    print("🎮 SERVO CONTROLLER GUI - DEMO MODE")
    print("="*60)
    print("✓ Running without serial hardware")
    print("✓ All features available for testing")
    print("✓ Try the ARM Robot tab for 6DOF control with animation!")
    print("✓ Click '🎬 Demo Sequence' for automatic demonstration")
    print("="*60 + "\n")
    
    root.mainloop()

if __name__ == "__main__":
    main()
