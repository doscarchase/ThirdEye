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
            # Create a basic readme or init if needed
            with open(os.path.join(PLUGIN_DIR, "__init__.py"), "w") as f:
                f.write("")

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