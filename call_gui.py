#!/usr/bin/env python3
"""
Simple GUI for controlling ElevenLabs conversational calls.
Provides Start Call and Hangup buttons to avoid terminal keyboard conflicts.
"""

import tkinter as tk
from tkinter import ttk
import threading


class CallControlGUI:
    """Simple GUI with Start and Hangup buttons for call control."""
    
    def __init__(self, on_start_call=None, on_hangup=None):
        """
        Initialize the GUI.
        
        Args:
            on_start_call: Callback function to execute when Start Call is pressed
            on_hangup: Callback function to execute when Hangup is pressed
        """
        self.on_start_call = on_start_call
        self.on_hangup = on_hangup
        self.call_active = False
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("ElevenLabs Call Control")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Configure style
        style = ttk.Style()
        style.configure("Start.TButton", font=("Arial", 14), padding=10)
        style.configure("Hangup.TButton", font=("Arial", 14), padding=10)
        style.configure("Status.TLabel", font=("Arial", 12), padding=10)
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title label
        title_label = ttk.Label(
            main_frame, 
            text="🎙️ ElevenLabs Call Control",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="Ready to start call",
            style="Status.TLabel",
            foreground="green"
        )
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Start Call button
        self.start_button = ttk.Button(
            main_frame,
            text="📞 Start Call",
            command=self._handle_start_call,
            style="Start.TButton"
        )
        self.start_button.grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # Hangup button (initially disabled)
        self.hangup_button = ttk.Button(
            main_frame,
            text="📴 Hangup",
            command=self._handle_hangup,
            style="Hangup.TButton",
            state="disabled"
        )
        self.hangup_button.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # Info label
        info_label = ttk.Label(
            main_frame,
            text="Click buttons to control call\nWindow can stay open during call",
            font=("Arial", 10),
            foreground="gray"
        )
        info_label.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.closed = False
    
    def _handle_start_call(self):
        """Handle Start Call button press."""
        if self.on_start_call and not self.call_active:
            self.call_active = True
            self.start_button.config(state="disabled")
            self.hangup_button.config(state="normal")
            self.status_label.config(text="Call in progress...", foreground="blue")
            
            # Run callback in separate thread to avoid blocking GUI
            threading.Thread(target=self.on_start_call, daemon=True).start()
    
    def _handle_hangup(self):
        """Handle Hangup button press."""
        if self.on_hangup and self.call_active:
            self.hangup_button.config(state="disabled")
            self.status_label.config(text="Hanging up...", foreground="orange")
            
            # Run callback in separate thread
            threading.Thread(target=self.on_hangup, daemon=True).start()
    
    def call_ended(self):
        """Update GUI when call ends (call from main thread)."""
        if not self.closed:
            self.root.after(0, self._update_call_ended)
    
    def _update_call_ended(self):
        """Internal method to update GUI on main thread."""
        self.call_active = False
        self.start_button.config(state="normal")
        self.hangup_button.config(state="disabled")
        self.status_label.config(text="Call ended", foreground="green")
    
    def update_status(self, message, color="black"):
        """Update status label with custom message."""
        if not self.closed:
            self.root.after(0, lambda: self._update_status(message, color))
    
    def _update_status(self, message, color):
        """Internal method to update status on main thread."""
        self.status_label.config(text=message, foreground=color)
    
    def _on_closing(self):
        """Handle window close event."""
        self.closed = True
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()
    
    def destroy(self):
        """Destroy the GUI window."""
        if not self.closed:
            self.closed = True
            self.root.quit()
            self.root.destroy()


def demo_gui():
    """Demo function showing how to use the GUI."""
    import time
    
    def start_call():
        print("🎙️ Starting call...")
        time.sleep(3)  # Simulate call
        print("📞 Call connected!")
    
    def hangup():
        print("📴 Hanging up call...")
        time.sleep(1)  # Simulate hangup
        print("✅ Call ended")
        gui.call_ended()
    
    gui = CallControlGUI(on_start_call=start_call, on_hangup=hangup)
    
    print("\n" + "="*50)
    print("📱 Call Control GUI Demo")
    print("="*50)
    print("\n✅ GUI window opened!")
    print("   Click 'Start Call' to begin")
    print("   Click 'Hangup' to end call")
    print("\nClose the window to exit.\n")
    
    gui.run()
    print("\n👋 GUI closed")


if __name__ == "__main__":
    demo_gui()
