import bpy
import json
from bpy.props import *
from .package_installation import is_pip_installed, is_package_installed
from .ptvsd_server import get_active_ptvsd_port, ptvsd_debugger_is_attached
from . import communication

class MyPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    package_name_to_install: StringProperty("Package Name to Install")
    addon_to_reload: StringProperty("Addon to Reload")
    script_path: StringProperty("Script Path")

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        if not is_pip_installed():
            layout.operator("development.install_pip")
        else:
            row = layout.row(align=True)
            row.prop(self, "package_name_to_install", text="Install Package")
            props = row.operator("development.install_python_package", text="", icon='IMPORT')
            props.package_name = self.package_name_to_install

            if not is_package_installed("ptvsd"):
                props = layout.operator("development.install_python_package", text="Install ptvsd (Python Debugger)")
                props.package_name = "ptvsd"

        ptvsd_port = get_active_ptvsd_port()
        if is_package_installed("ptvsd"):
            if ptvsd_port is None:
                layout.operator("development.start_ptvsd_server")
            else:
                layout.label(text=f"ptvsd is running at port {ptvsd_port}")
                if ptvsd_debugger_is_attached():
                    layout.label(text="Debugger is attached")

        row = layout.row(align=True)
        row.prop(self, "addon_to_reload", text="Reload Addon")
        props = row.operator("development.reload_addon", text="", icon='FILE_REFRESH')
        props.module_name = self.addon_to_reload

        row = layout.row(align=True)
        row.prop(self, "script_path", text="Run External Script")
        props = row.operator("development.run_external_script", text="", icon='PLAY')
        props.filepath = self.script_path

        communication_port = communication.get_server_port()
        if communication_port is None:
            layout.operator("development.start_server")
        else:
            layout.label(text=f"Server is running at port {communication_port}")

        if ptvsd_port is not None or communication_port is not None:
            layout.operator("development.copy_connection_info")

        vscode_address = communication.get_vscode_address()
        if vscode_address is None:
            layout.label(text="Not connected to vscode.")
        else:
            layout.label(text=f"Connected to vscode at {vscode_address}")


def send_connection_info():
    info = get_connection_info()
    communication.send_command('/set_connection_info', info)

def get_connection_info():
    ptvsd_port = get_active_ptvsd_port()
    communication_port = communication.get_server_port()
    info = {
        "host": "localhost",
        "ptvsd_port": ptvsd_port,
        "communication_port": communication_port,
    }
    return info

class CopyConnectionInfoOperator(bpy.types.Operator):
    bl_idname = "development.copy_connection_info"
    bl_label = "Copy Connection Info"
    bl_description = "Copy connection information that can be pasted into vscode"

    def execute(self, context):
        info = get_connection_info()
        context.window_manager.clipboard = json.dumps(info)
        return {'FINISHED'}
