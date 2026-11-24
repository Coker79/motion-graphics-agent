"""toykit.camera: one camera rig for 9:16 Shorts: eased position + aim keys (Bezier, eased at BOTH ends), lens and
focus pulls, DOF locked to a focus empty (usually on a character's face) and an optional handheld drift."""
import bpy, math
from mathutils import Vector


def fcurves(idb):
    """all F-curves of an ID's action (Blender 4.4+/5 layered actions, falling back to legacy action.fcurves)."""
    ad = getattr(idb, 'animation_data', None)
    if not ad or not ad.action: return []
    act = ad.action
    try:
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
        return list(cb.fcurves) if cb else []
    except Exception:
        return list(getattr(act, 'fcurves', []))


class Cam:
    def __init__(self, sc, lens=35.0, fstop=2.4, name='CAM'):
        self.sc = sc
        self.cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(self.cam); sc.camera = self.cam
        self.aim = bpy.data.objects.new(name + '_aim', None); sc.collection.objects.link(self.aim)
        c = self.cam.constraints.new('TRACK_TO'); c.target = self.aim; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
        d = self.cam.data; d.lens = lens; d.clip_start = 0.03; d.clip_end = 800; d.sensor_fit = 'AUTO'; d.sensor_width = 36
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop; d.dof.aperture_blades = 7
        self.focus = bpy.data.objects.new(name + '_focus', None); sc.collection.objects.link(self.focus); d.dof.focus_object = self.focus

    def key(self, f, pos=None, aim=None, lens=None, fstop=None, roll=None):
        if pos is not None: self.cam.location = pos; self.cam.keyframe_insert('location', frame=f)
        if aim is not None: self.aim.location = aim; self.aim.keyframe_insert('location', frame=f)
        if lens is not None: self.cam.data.lens = lens; self.cam.data.keyframe_insert('lens', frame=f)
        if fstop is not None: self.cam.data.dof.aperture_fstop = fstop; self.cam.data.dof.keyframe_insert('aperture_fstop', frame=f)
        if roll is not None:
            self.aim.rotation_euler = (0, 0, math.radians(roll)); self.aim.keyframe_insert('rotation_euler', frame=f)
        return self

    def focus_on(self, obj, offset=(0, 0, 0), bone=None):
        """focus empty rides `obj` (or an armature bone) at a local offset."""
        self.focus.parent = obj
        if bone: self.focus.parent_type = 'BONE'; self.focus.parent_bone = bone
        self.focus.location = offset; return self

    def ease(self, slow_in=True, slow_out=True):
        """all camera keys eased (auto-clamped Bezier); positional moves never start or stop abruptly."""
        for idb in (self.cam, self.aim, self.cam.data):
            for fc in fcurves(idb):
                for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
                fc.update()
        return self

    def handheld(self, amp=0.006, scale=28.0, seed=1):
        """subtle organic drift on the aim (and a little on the position): the camera is never dead still."""
        for idb, a in ((self.aim, amp), (self.cam, amp * 0.5)):
            if not fcurves(idb): idb.keyframe_insert('location', frame=self.sc.frame_start)
            for i, fc in enumerate(fc for fc in fcurves(idb) if fc.data_path == 'location'):
                m = fc.modifiers.new('NOISE'); m.scale = scale; m.strength = a; m.phase = seed * 7.3 + i * 13.1; m.depth = 1
        return self
