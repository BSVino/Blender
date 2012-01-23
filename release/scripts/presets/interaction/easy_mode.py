import bpy
user_preferences = bpy.context.user_preferences

user_preferences.view.show_tooltips_python = False
user_preferences.view.use_rotate_around_active = True
user_preferences.view.hide_3d_cursor = True
user_preferences.edit.use_drag_immediately = False
user_preferences.edit.use_insertkey_xyz_to_rgb = True
user_preferences.inputs.invert_mouse_zoom = False
user_preferences.inputs.select_mouse = 'LEFT'
user_preferences.inputs.use_emulate_numpad = False
user_preferences.inputs.use_mouse_continuous = False
user_preferences.inputs.use_mouse_emulate_3_button = False
user_preferences.inputs.view_rotate_method = 'TURNTABLE'
user_preferences.inputs.view_zoom_axis = 'VERTICAL'
user_preferences.inputs.view_zoom_method = 'DOLLY'
