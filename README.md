# Gravity Collider Bone Physics for Blender

A cloth-based bone collider plugin for animating armatures with physics. This setup works only on connected joint chains. Non-connected bones will require separate colliders.

Demonstration: https://www.youtube.com/watch?v=DY9i0HolVmI

Based on the physics setup shown here:
https://www.youtube.com/watch?v=uV5DE0CkUow


## How to use:
![](https://github.com/MiniEval/Bone-Physics/blob/main/UI.PNG)

1. Select bones in edit mode.
2. Click "Initialise Collision Boxes" to create collision boxes for each selected bone
3. Scale and roll collision boxes to desired transforms.
4. Click "Bake Collision Boxes" to set up rig. "Bake with Pole Targets" can be selected to respect the rotation of collision boxes in the physics simulation (may result in undesired twisting).
5. (Optional) Fine-tune the "pin" vertex group of the collider object to meet stiffness requirements.
