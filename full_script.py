import maya.cmds as cmds
import random
import functools

def createUI( pWindowTitle, pApplyCallback ):

    windowID = 'cells_window'

    if cmds.window( windowID, exists=True ):
        cmds.deleteUI( windowID )

    cmds.window( windowID, title=pWindowTitle, sizeable=False, resizeToFitChildren=True )

    #determines layout for UI, columnWidth =[(column_index, width in px)...]
    cmds.rowColumnLayout( numberOfColumns=2, columnWidth=[ (1,100), (2,100) ])

    cmds.text( label='Num Blood Cells:' )

    num_shield_pieces = cmds.intField(value = 50)

    cmds.separator( h=10, style='none' ) #blank space, for aesthetics
    cmds.separator( h=10, style='none' )
    cmds.separator( h=10, style='none' )
    cmds.separator( h=10, style='none' )

    cmds.button( label='Animate', command=functools.partial( pApplyCallback,
                                                  num_shield_pieces,
                                                  windowID ) )
    def cancelCallback( *pArgs ):
        if cmds.window( windowID, exists=True ):
            cmds.deleteUI( windowID )

    cmds.button( label='Exit', command=cancelCallback )

    cmds.showWindow()

def applyCallback(  p_num_shield_pieces, p_window_ID, *pArgs ):

    p_num_shield_pieces = cmds.intField( p_num_shield_pieces, query=True, value=True )

    #deletes the UI window once generate has been pressed
    if cmds.window( p_window_ID, exists=True ):
        cmds.deleteUI( p_window_ID )

    #run the rest of the script once generate has been pressed
    run_script(p_num_shield_pieces)


def applyMaterial(p_object, p_color, p_shader_type):
    if cmds.objExists(p_object):

        shd = cmds.shadingNode(p_shader_type, name="%s_%s" % (p_object, p_shader_type), asShader=True)

        #p_color is a list of [r,b,g]
        cmds.setAttr(shd+".color", p_color[0],  p_color[1],  p_color[2], type="double3")
        shdSG = cmds.sets(name='%sSG' % shd, empty=True, renderable=True, noSurfaceShader=True)

        cmds.connectAttr('%s.outColor' % shd, '%s.surfaceShader' % shdSG)
        cmds.sets(p_object, e=True, forceElement=shdSG)

#p_shield_shape is the shape to be duplicated
def generate_shield(p_shield_shape, p_num_shield_pieces):
    random.seed( 1234 ) #change seed

    transformName = p_shield_shape[0]

    instanceGroupName = cmds.group( empty=True, name=transformName + '_instance_grp#' )

    instance_group = []

    for i in range( 0, p_num_shield_pieces ):

        instanceResult = cmds.instance( transformName, name=transformName + '_instance#' )

        cmds.parent( instanceResult, instanceGroupName )

        #print 'instanceResult: ' + str( instanceResult )

        x = random.uniform( -10, 10 )
        y = random.uniform( 0, 20 )
        z = random.uniform( -10, 10 )

        cmds.move( x, y, z, instanceResult )

        xRot = random.uniform( 0, 360 )
        yRot = random.uniform( 0, 360 )
        zRot = random.uniform( 0, 360 )

        #cmds.rotate( xRot, yRot, zRot, instanceResult )

        scalingFactor = random.uniform( 0.3, 1.15 )

        cmds.scale( scalingFactor, 1.0, scalingFactor, instanceResult )

        instance_group.append(instanceResult)

    cmds.hide( transformName )

    cmds.xform( instanceGroupName, centerPivots=True )

    return instance_group, instanceGroupName

def aim_at_first(p_shield_core, p_shield_pieces):

    targetName = p_shield_core

    for objectName in p_shield_pieces:

        print 'Constraining %s towards %s' % ( objectName, targetName )

        cmds.aimConstraint( targetName, objectName, aimVector=[0,1,0] )


def key_rotation(p_rotation_obj, pTargetAttribute, p_time_in, p_time_out):

    #startTime = cmds.playbackOptions( query=True, minTime=True )
    #endTime = cmds.playbackOptions( query=True, maxTime=True )

    #print('object name', p_rotation_obj)

    cmds.cutKey( p_rotation_obj, time=(p_time_in, p_time_out), attribute=pTargetAttribute )

    cmds.setKeyframe( p_rotation_obj, time=p_time_in, attribute=pTargetAttribute, value=0 )

    cmds.setKeyframe( p_rotation_obj, time=p_time_out, attribute=pTargetAttribute, value=360 )

    cmds.selectKey( p_rotation_obj, time=(p_time_in, p_time_out), attribute=pTargetAttribute, keyframe=True )

    cmds.keyTangent( inTangentType='linear', outTangentType='linear' )

def expand_from_first(p_target, p_shield_pieces):

    targetName = p_target[0] #just get the target obj, not its underlying shape (led to error)

    locatorGroupName = cmds.group( empty=True, name='expansion_locator_grp#' )

    maxExpansion = 100

    newAttributeName = 'expansion'

    if not cmds.objExists( '%s.%s' % ( targetName, newAttributeName ) ):

        cmds.select( targetName )

        cmds.addAttr( longName=newAttributeName, shortName='exp',
                      attributeType='double', min=0, max=maxExpansion,
                      defaultValue=maxExpansion, keyable=True )

    for objectName in p_shield_pieces:

        #somehow the objects are each their own list, so just get the name of the obj
        objectName = objectName[0]

        coords = cmds.getAttr( '%s.translate' % ( objectName ) )[0]

        locatorName = cmds.spaceLocator( position=coords, name='%s_loc#' % ( objectName ) )[0]

        cmds.xform( locatorName, centerPivots=True )

        cmds.parent( locatorName, locatorGroupName )

        pointConstraintName = cmds.pointConstraint( [ targetName, locatorName ], objectName, name='%s_pointConstraint#' % ( objectName ) )[0]

        cmds.expression( alwaysEvaluate=True,
                         name='%s_attractWeight' % ( objectName ),
                         object=pointConstraintName,
                         string='%sW0=%s-%s.%s' % ( targetName, maxExpansion, targetName, newAttributeName ) )

        cmds.connectAttr( '%s.%s' % ( targetName, newAttributeName ),
                          '%s.%sW1' % ( pointConstraintName, locatorName ) )


    cmds.xform( locatorGroupName, centerPivots=True )

    return locatorGroupName

#ability to alter amount of expansion, useful for later
def expansion(p_shield_center, time_in, time_out, exp_in_value = 0, exp_out_value = 100):
    cmds.setKeyframe( p_shield_center, time=time_in, attribute='expansion', value=exp_in_value )

    cmds.setKeyframe( p_shield_center, time=time_out, attribute='expansion', value=exp_out_value )


def heartbeat(p_core, p_start_time):


    expansion(p_core, str(p_start_time) + 'sec', str(p_start_time) + '.5sec', 10, 100)
    expansion(p_core, str(p_start_time) + '.6sec', str(p_start_time + 1) + 'sec', 50, 100)
    #expansion(p_core, str(p_start_time + 1) + '.1sec', str(p_start_time + 1)+ '.2sec', 100, 80)

    expansion(p_core, str(p_start_time + 1) + '.1sec', str(p_start_time + 1) + '.9sec', 80, 10)

def run_script(num_shield_pieces = 50):
    RED = [1, 0, 0] #red blood cells
    BLUE = [0, 0, 1] #blue for the core, aka Sonic
    DARK_RED = [.545, 0, 0]
    main_light = cmds.directionalLight(name = "main_light", intensity = 5)
    cmds.move(-5.711, 14.564, 11.097, "main_light")
    cmds.rotate('-67.367deg', '-24.33deg', '54.557deg', "main_light")
    shield_shape = cmds.polyTorus (sr = 0.2, name="myRing#")
    shield_center = cmds.polyPlatonicSolid (radius=2.55, st=1, name="core")
    applyMaterial(shield_center[0], DARK_RED, 'lambert')
    cmds.move(0, 9, 0, "core") #move the core higher

    core_piece_1 = cmds.polyCylinder(name="tube_1")
    applyMaterial(core_piece_1[0], BLUE, 'lambert')
    cmds.move(0.195, 11.014, -1.221, "tube_1")
    cmds.rotate('-30.351deg', 0, 0, "tube_1")
    cmds.scale(0.505, 0.619, 0.505, "tube_1")

    core_piece_2 = cmds.polyCylinder(name="tube_2")
    applyMaterial(core_piece_2[0], RED, 'lambert')
    cmds.move(-0.917, 11.185, -0.216, "tube_2")
    cmds.rotate('-3.436deg', '14.201deg', '24.834deg', "tube_2")
    cmds.scale(0.505, 0.619, 0.505, "tube_2")

    shield_pieces, shield_pieces_group = generate_shield(shield_shape, num_shield_pieces)

    #shield_piece_color = [.83, .69, .22] #gold for the rings
    for piece_obj in shield_pieces:
        applyMaterial(piece_obj[0], RED, 'phong')

    aim_at_first(shield_center, shield_pieces)

    locator_group = expand_from_first(shield_center, shield_pieces)

    cmds.parent(locator_group, shield_pieces_group)

    startTime = cmds.playbackOptions( query=True, minTime=True )
    endTime = cmds.playbackOptions( query=True, maxTime=True )

    #second param is rotation param
    key_rotation(shield_pieces_group, 'rotateY', startTime, endTime)

    cmds.cutKey( shield_center, time=(startTime, endTime), attribute='expansion')

    heartbeat(shield_center, 0)
    heartbeat(shield_center, 2)
    heartbeat(shield_center, 4)
    heartbeat(shield_center, 6)
    heartbeat(shield_center, 8)
    heartbeat(shield_center, 10)

    cmds.selectKey( shield_center, time=(startTime, endTime), attribute='expansion', keyframe=True )

    cmds.keyTangent( inTangentType='linear', outTangentType='linear' )

if __name__ == '__main__':

    cmds.playbackOptions( minTime='0sec', maxTime='12sec' )

    createUI( 'Blood Cells', applyCallback )
