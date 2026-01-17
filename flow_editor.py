# ----------------------------------------------------------------------------
#  ThirdEye AI Vision Suite - Proprietary and Confidential
#  Copyright (c) 2026 Devon Chase. All rights reserved.
# ----------------------------------------------------------------------------
import customtkinter as ctk
import os

class FlowEditor(ctk.CTkToplevel):
    def __init__(self, parent, model_name, automation_manager):
        super().__init__(parent)
        self.title(f"Automation Flow: {model_name}")
        self.geometry("600x700")
        self.model_name = model_name
        self.manager = automation_manager
        
        # Load existing flow data
        self.flow_data = self.manager.get_flow_for_model(model_name)
        
        self.attributes("-topmost", True)
        
        # --- HEADER ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(header, text=f"Reaction Chain: {model_name}", 
                    font=("Roboto", 20, "bold")).pack(side="left")
        
        # Save/Load Buttons
        ctk.CTkButton(header, text="Load Preset", width=100, fg_color="#555555",
                     command=self._load_preset_popup).pack(side="right", padx=5)
        ctk.CTkButton(header, text="Save Preset", width=100,
                     command=self._save_preset_popup).pack(side="right", padx=5)

        # --- SCROLLABLE AREA (The Flow Chart) ---
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.step_widgets = [] # Keep track of UI elements to read values later
        self._render_flow()

        # --- FOOTER (Add Button) ---
        footer = ctk.CTkFrame(self, fg_color="transparent", height=60)
        footer.pack(fill="x", padx=20, pady=20)
        
        add_btn = ctk.CTkButton(footer, text="+ Add Reaction Step", fg_color="green", 
                               height=40, font=("Roboto", 14, "bold"),
                               command=self._add_step)
        add_btn.pack(fill="x")
        
        apply_btn = ctk.CTkButton(footer, text="Apply & Close", fg_color="#3B8ED0",
                                command=self._apply_changes)
        apply_btn.pack(fill="x", pady=5)

    def _render_flow(self):
        """Re-draws the entire list based on self.flow_data."""
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self.step_widgets.clear()
        
        available_scripts = self.manager.get_available_scripts()
        if not available_scripts:
            available_scripts = ["No scripts in /plugins"]

        for index, data in enumerate(self.flow_data):
            # 1. Draw Arrow (if not first)
            if index > 0:
                arrow = ctk.CTkLabel(self.scroll, text="↓", font=("Arial", 24, "bold"), text_color="gray")
                arrow.pack(pady=0)

            # 2. Draw Card
            card = ctk.CTkFrame(self.scroll, border_width=1, border_color="#444444")
            card.pack(fill="x", pady=5, padx=5)
            
            # Row 1: Title + Remove
            row1 = ctk.CTkFrame(card, fg_color="transparent")
            row1.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(row1, text=f"Step {index + 1}", font=("Roboto", 12, "bold"), text_color="#3B8ED0").pack(side="left")
            ctk.CTkButton(row1, text="✕", width=30, fg_color="transparent", text_color="red", hover_color="#330000",
                         command=lambda i=index: self._remove_step(i)).pack(side="right")

            # Row 2: Script Selection
            row2 = ctk.CTkFrame(card, fg_color="transparent")
            row2.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(row2, text="Script:", width=60, anchor="w").pack(side="left")
            
            script_var = ctk.StringVar(value=data.get("script", available_scripts[0]))
            dropdown = ctk.CTkOptionMenu(row2, values=available_scripts, variable=script_var)
            dropdown.pack(side="left", fill="x", expand=True)

            # Row 3: Parameters (Delay & Args)
            row3 = ctk.CTkFrame(card, fg_color="transparent")
            row3.pack(fill="x", padx=10, pady=(5, 10))
            
            # Delay
            ctk.CTkLabel(row3, text="Wait (s):").pack(side="left", padx=(0,5))
            delay_entry = ctk.CTkEntry(row3, width=50)
            delay_entry.insert(0, str(data.get("delay", 0)))
            delay_entry.pack(side="left")
            
            # Args
            ctk.CTkLabel(row3, text="Args:").pack(side="left", padx=(15, 5))
            args_entry = ctk.CTkEntry(row3)
            args_entry.insert(0, data.get("args", ""))
            args_entry.pack(side="left", fill="x", expand=True)
            
            # Store references to read later
            self.step_widgets.append({
                "script": script_var,
                "delay": delay_entry,
                "args": args_entry
            })

    def _add_step(self):
        # Save current state from UI to data first
        self._scrape_ui_to_data()
        # Add empty step
        self.flow_data.append({"script": "", "delay": 0, "args": ""})
        self._render_flow()

    def _remove_step(self, index):
        self._scrape_ui_to_data()
        self.flow_data.pop(index)
        self._render_flow()

    def _scrape_ui_to_data(self):
        """Reads values from active widgets back into self.flow_data"""
        new_data = []
        for widgets in self.step_widgets:
            try:
                d_val = float(widgets["delay"].get())
            except:
                d_val = 0.0
                
            step = {
                "script": widgets["script"].get(),
                "delay": d_val,
                "args": widgets["args"].get()
            }
            new_data.append(step)
        self.flow_data = new_data

    def _apply_changes(self):
        self._scrape_ui_to_data()
        self.manager.set_flow_for_model(self.model_name, self.flow_data)
        self.destroy()

    def _save_preset_popup(self):
        self._scrape_ui_to_data()
        dialog = ctk.CTkInputDialog(text="Preset Name:", title="Save Flow")
        # Fix z-order
        dialog.attributes("-topmost", True)
        name = dialog.get_input()
        if name:
            self.manager.set_flow_for_model(self.model_name, self.flow_data)
            path = self.manager.save_flow_preset(self.model_name, name)
            print(f"Saved to {path}")

    def _load_preset_popup(self):
        # Scan dir
        path = f"user_configs/{self.model_name}/flows"
        if not os.path.exists(path): os.makedirs(path)
        files = [f.replace(".json","") for f in os.listdir(path) if f.endswith(".json")]
        
        if not files:
            print("No presets found")
            return

        # Simple separate window for list
        top = ctk.CTkToplevel(self)
        top.geometry("250x300")
        top.title("Load Flow")
        top.attributes("-topmost", True)
        
        ctk.CTkLabel(top, text="Select Preset:").pack(pady=10)
        
        for f in files:
            ctk.CTkButton(top, text=f, command=lambda n=f: self._perform_load(n, top)).pack(pady=2, padx=20, fill="x")

    def _perform_load(self, name, window):
        if self.manager.load_flow_preset(self.model_name, name):
            self.flow_data = self.manager.get_flow_for_model(self.model_name)
            self._render_flow()
        window.destroy()