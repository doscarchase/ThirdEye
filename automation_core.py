# ----------------------------------------------------------------------------
#  ThirdEye AI Vision Suite - Proprietary and Confidential
#  Copyright (c) 2026 Devon Chase. All rights reserved.
# ----------------------------------------------------------------------------
import os
import json
import time
import importlib
import threading
import inspect

PLUGIN_DIR = "plugins"

class AutomationManager:
    def __init__(self):
        self.plugins = {}
        self.active_flows = {} # { model_name: [step_data, step_data...] }
        self._ensure_plugin_dir()
        self.refresh_plugins()

    def _ensure_plugin_dir(self):
        if not os.path.exists(PLUGIN_DIR):
            os.makedirs(PLUGIN_DIR)
        
        # Ensure __init__.py exists
        init_path = os.path.join(PLUGIN_DIR, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write("")

        # Define Default Plugins content
        # We use inspect.cleandoc ensures indentation is removed regardless of how you copy/paste
        defaults = {
            "visual_flash.py": r'''
                """
                Simulates a visual flash (Argument: 'color=red' or 'color=white')
                """
                def run(context, args):
                    color = "white"
                    if "red" in args: color = "red"
                    print(f"[SCRIPT] VISUAL FLASH ACTIVATED: {color.upper()}")
                ''',
            "system_alert.py": r'''
                """
                Plays a system beep and prints a message.
                """
                import os

                def run(context, args):
                    print(f"[SCRIPT] System Alert Triggered by {context.get('identity')}!")
                    if os.name == 'nt':
                        import winsound
                        winsound.Beep(1000, 500)
                    else:
                        print("\a")
                ''',
            "camera_snapshot.py": r'''
                """
                Saves the current frame to the 'snapshots' directory.
                Argument: 'prefix=my_name' (optional)
                """
                import cv2
                import os
                import time

                def run(context, args):
                    frame = context.get("frame")
                    if frame is None:
                        print("[SNAPSHOT] Error: No frame data in context.")
                        return

                    # Parse args for custom prefix
                    prefix = "snapshot"
                    if "prefix=" in args:
                        parts = args.split("prefix=")
                        if len(parts) > 1:
                            prefix = parts[1].split(" ")[0]

                    save_dir = "snapshots"
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                        
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"{prefix}_{timestamp}.jpg"
                    filepath = os.path.join(save_dir, filename)
                    
                    try:
                        cv2.imwrite(filepath, frame)
                        print(f"[SNAPSHOT] Saved: {filepath}")
                    except Exception as e:
                        print(f"[SNAPSHOT] Save failed: {e}")
                '''
        }

        # Create defaults if they don't exist
        for filename, content in defaults.items():
            path = os.path.join(PLUGIN_DIR, filename)
            if not os.path.exists(path):
                with open(path, "w") as f:
                    # inspect.cleandoc fixes the indentation error
                    f.write(inspect.cleandoc(content))
                    print(f"Created default plugin: {filename}")

    def refresh_plugins(self):
        """Scans the plugins folder for python scripts with a 'run' function."""
        self.plugins = {}
        for f in os.listdir(PLUGIN_DIR):
            if f.endswith(".py") and f != "__init__.py":
                mod_name = f[:-3]
                try:
                    module = importlib.import_module(f"{PLUGIN_DIR}.{mod_name}")
                    importlib.reload(module) # Ensure fresh code
                    if hasattr(module, "run"):
                        # Get docstring for UI description
                        desc = module.__doc__.strip() if module.__doc__ else "No description."
                        self.plugins[mod_name] = {"func": module.run, "desc": desc}
                except Exception as e:
                    print(f"Failed to load plugin {mod_name}: {e}")

    def get_available_scripts(self):
        return list(self.plugins.keys())

    def get_flow_for_model(self, model_name):
        return self.active_flows.get(model_name, [])

    def set_flow_for_model(self, model_name, flow_data):
        """
        flow_data is a list of dicts:
        [
            {"script": "sound_alert", "delay": 0, "args": "volume=100"},
            {"script": "log_event", "delay": 5, "args": ""}
        ]
        """
        self.active_flows[model_name] = flow_data

    def save_flow_preset(self, model_name, preset_name):
        path = f"user_configs/{model_name}/flows"
        if not os.path.exists(path):
            os.makedirs(path)
        
        filepath = os.path.join(path, f"{preset_name}.json")
        with open(filepath, "w") as f:
            json.dump(self.active_flows.get(model_name, []), f, indent=4)
        return filepath

    def load_flow_preset(self, model_name, preset_name):
        path = f"user_configs/{model_name}/flows/{preset_name}.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                self.active_flows[model_name] = data
                return True
        return False

    def trigger_flow(self, model_name, context_data):
        """
        Executes the flow associated with the model in a background thread.
        context_data: dict containing {identity, confidence, timestamp, etc}
        """
        flow = self.active_flows.get(model_name)
        if not flow:
            return

        # Run in thread to allow delays without freezing UI
        threading.Thread(target=self._execute_chain, args=(flow, context_data), daemon=True).start()

    def _execute_chain(self, flow, context):
        print(f"--- Starting Automation Chain for {context.get('identity')} ---")
        
        for step in flow:
            script_name = step.get("script")
            delay = float(step.get("delay", 0))
            args = step.get("args", "")

            # 1. Handle Delay
            if delay > 0:
                time.sleep(delay)

            # 2. Execute Script
            plugin = self.plugins.get(script_name)
            if plugin:
                try:
                    # Pass context + user args
                    plugin["func"](context, args)
                except Exception as e:
                    print(f"Error executing {script_name}: {e}")
            else:
                print(f"Script {script_name} not found.")
