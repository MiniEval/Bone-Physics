bl_info = {
    "name": "Gravity Collider Bone Physics",
    "description": "Workflow automation of cloth-based bone collider setups for armature bones.",
    "author": "MiniEval_, AZmaybe9",
    "location": "View3D > Toolshelf > Bone Physics",
    "blender": (2, 92, 0),
    "category": "Physics",
    "tracker_url": "https://github.com/MiniEval/Bone-Physics",
    "support": "COMMUNITY",
    "version": (1, 0, 2)
}


modulesNames = ['base_manager', 'operators', 'mesh_helpers']

import sys
import importlib

modulesFullNames = {}
for currentModuleName in modulesNames:
    modulesFullNames[currentModuleName] = ('{}.{}'.format(__name__, currentModuleName))

for currentModuleFullName in modulesFullNames.values():
    if currentModuleFullName in sys.modules:
        importlib.reload(sys.modules[currentModuleFullName])
    else:
        globals()[currentModuleFullName] = importlib.import_module(currentModuleFullName)
        setattr(globals()[currentModuleFullName], 'modulesNames', modulesFullNames)


def register():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()


def unregister():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()


if __name__ == "__main__":
    register()