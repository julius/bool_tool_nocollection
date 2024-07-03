import bpy
from ..functions import (
    basic_poll,
    object_visibility_set,
    list_canvases,
    list_selected_cutters,
    list_canvas_cutters,
    list_canvas_slices,
    delete_empty_collection,
    filter_unused_cutters,
)


#### ------------------------------ OPERATORS ------------------------------ ####

# Toggle Boolean Cutter
class OBJECT_OT_toggle_boolean_brush(bpy.types.Operator):
    bl_idname = "object.toggle_boolean_brush"
    bl_label = "Toggle Boolean Cutter"
    bl_description = "Toggle this boolean cutter. If cutter isn't the active object it will be toggled for every canvas that uses it"
    bl_options = {'UNDO'}

    specified_cutter: bpy.props.StringProperty(
    )
    specified_canvas: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    def execute(self, context):
        if self.specified_cutter:
            canvas = [bpy.data.objects[self.specified_canvas]]
            brushes = [bpy.data.objects[self.specified_cutter]]
        else:
            canvas = list_canvases()
            brushes = list_selected_cutters(context)

        if brushes:
            for obj in canvas:
                # toggle_slices_visibility
                if obj.booleans.slice == True:
                    if any(modifier.object in brushes for modifier in obj.modifiers):
                        obj.hide_viewport = not obj.hide_viewport
                        obj.hide_render = not obj.hide_render

                # toggle_modifiers_visibility
                for modifier in obj.modifiers:
                    if "boolean_" in modifier.name:
                        if modifier.object in brushes:
                            modifier.show_viewport = not modifier.show_viewport
                            modifier.show_render = not modifier.show_render

        else:
            self.report({'INFO'}, "No boolean cutters are selected")

        return {'FINISHED'}


# Remove Boolean Cutter
class OBJECT_OT_remove_boolean_brush(bpy.types.Operator):
    bl_idname = "object.remove_boolean_brush"
    bl_label = "Remove Boolean Cutter"
    bl_description = "Remove this boolean cutter. If cutter isn't the active object it will be removed from every canvas that uses it"
    bl_options = {'UNDO'}

    method: bpy.props.EnumProperty(
        name = "Method",
        items = (('ALL', "All", "Remove cutter from all canvases that use it"),
                 ('SPECIFIED', "Specified", "Remove cutter from specified canvas")),
        default = 'ALL',
    )

    specified_cutter: bpy.props.StringProperty(
    )
    specified_canvas: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    def execute(self, context):
        if self.method == 'SPECIFIED':
            canvas = [bpy.data.objects[self.specified_canvas]]
            cutters = [bpy.data.objects[self.specified_cutter]]
            slices = list_canvas_slices(canvas)
        elif self.method == 'ALL':
            canvas = list_canvases()
            cutters = list_selected_cutters(context)

        if cutters:
            # Remove Modifiers
            for obj in canvas:
                for modifier in obj.modifiers:
                    if "boolean_" in modifier.name:
                        if modifier.object in cutters:
                            obj.modifiers.remove(modifier)

                # remove_canvas_property_if_needed
                other_cutters, __ = list_canvas_cutters([obj])
                if len(other_cutters) == 0:
                    obj.booleans.canvas = False

                # Remove Slices (for_all_method)
                if obj.booleans.slice == True:
                    bpy.data.objects.remove(obj)


            if self.method == 'SPECIFIED':
                # Remove Slices (for_specified_method)
                for obj in slices:
                    for mod in obj.modifiers:
                        if mod.type == 'BOOLEAN' and mod.object in cutters:
                            bpy.data.objects.remove(obj)

                filter_unused_cutters(cutters, canvas)

            for cutter in cutters:
                # restore_cutter_visibility
                cutter.display_type = 'TEXTURED'
                object_visibility_set(cutter, value=True)
                cutter.hide_render = False
                cutter.booleans.cutter = ""

                # remove_cutter_parent_&_collection
                cutter.parent = None
                cutters_collection = bpy.data.collections.get("boolean_cutters")
                if cutters_collection in cutter.users_collection:
                    bpy.data.collections.get("boolean_cutters").objects.unlink(cutter)

            # purge_empty_collection
            delete_empty_collection()

        else:
            self.report({'INFO'}, "No boolean cutters are selected")

        return {'FINISHED'}


# Apply Boolean Cutter
class OBJECT_OT_apply_boolean_brush(bpy.types.Operator):
    bl_idname = "object.apply_boolean_brush"
    bl_label = "Apply Boolean Cutter"
    bl_description = "Apply this boolean cutter. If cutter isn't the active object it will be applied to every canvas that uses it"
    bl_options = {'UNDO'}

    method: bpy.props.EnumProperty(
        name = "Method",
        items = (('ALL', "All", "Remove cutter from all canvases that use it"),
                 ('SPECIFIED', "Specified", "Remove cutter from specified canvas")),
        default = 'ALL',
    )

    specified_cutter: bpy.props.StringProperty(
    )
    specified_canvas: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    def execute(self, context):
        if self.method == 'SPECIFIED':
            canvas = [bpy.data.objects[self.specified_canvas]]
            cutters = [bpy.data.objects[self.specified_cutter]]
            slices = list_canvas_slices(canvas)
        elif self.method == 'ALL':
            canvas = list_canvases()
            cutters = list_selected_cutters(context)

        if cutters:
            # Apply Modifiers
            for obj in canvas:
                context.view_layer.objects.active = obj
                for mod in obj.modifiers:
                    if "boolean_" in mod.name:
                        if mod.object in cutters:
                            try:
                                bpy.ops.object.modifier_apply(modifier=mod.name)
                            except:
                                context.active_object.data = context.active_object.data.copy()
                                bpy.ops.object.modifier_apply(modifier=mod.name)

                # remove_canvas_property_if_needed
                other_cutters, __ = list_canvas_cutters([obj])
                if len(other_cutters) == 0:
                    obj.booleans.canvas = False
                obj.booleans.slice = False


            if self.method == 'SPECIFIED':
                # Apply Modifier for Slices (for_specified_method)
                for obj in slices:
                    for mod in obj.modifiers:
                        if mod.type == 'BOOLEAN' and mod.object in cutters:
                            context.view_layer.objects.active = obj
                            bpy.ops.object.modifier_apply(modifier=mod.name)

                filter_unused_cutters(cutters, canvas)

            # purge_orphaned_brushes
            for cutter in cutters:
                orphaned_mesh = cutter.data
                bpy.data.objects.remove(cutter)
                bpy.data.meshes.remove(orphaned_mesh)

            # purge_empty_collection
            delete_empty_collection()

        else:
            self.report({'INFO'}, "No boolean cutters are selected")

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = (
    OBJECT_OT_toggle_boolean_brush,
    OBJECT_OT_remove_boolean_brush,
    OBJECT_OT_apply_boolean_brush,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
