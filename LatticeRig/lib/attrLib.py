import maya.cmds as mc
import maya.api.OpenMaya as om2



def swapOut(oldAttr, newAttr):
    oldOuts = mc.listConnections(oldAttr, s=False, d=True, plugs=True)
    newOuts = mc.listConnections(newAttr, s=False, d=True, plugs=True)
    for out in oldOuts:
        connectAttr(newAttr, out)
    for out in newOuts:
        connectAttr(oldAttr, out)


def disconnectAttr(attr, ignoreMissingAttrs=False):
    # do actual work
    if ignoreMissingAttrs:
        node, longName = attr.split('.', 1)
        if '.' in longName:
            longName = longName.split('.')[-1]
        if not mc.attributeQuery(longName, node=node, exists=True):
            return

    # is attribute locked?
    locked = mc.getAttr(attr, lock=True)
    if locked:
        mc.setAttr(attr, lock=False)

    inputs = mc.listConnections(attr, s=True, d=False, plugs=True)
    if not inputs:
        return
    mc.disconnectAttr(inputs[0], attr)

    # lock again if was locked
    if locked:
        mc.setAttr(attr, lock=True)


def lockHideAttrs(node, attrs, lock=True, hide=True):
    attrs = flattenAttrs(attrs)
    for a in attrs:
        mc.setAttr(node + '.' + a, lock=lock, k=not hide, ch=not hide)


def unlock(nodes, attrs):
    if isinstance(nodes, basestring):
        nodes = [nodes]
    attrs = flattenAttrs(attrs)
    [mc.setAttr(node + '.' + a, lock=False, k=True) for a in attrs for node in nodes]


def flattenAttrs(attrs):
    shortAttrs = ['t', 'r', 's']
    axis = ['x', 'y', 'z']
    flatAttrs = []
    for a in attrs:
        if a in shortAttrs:
            for axes in axis:
                flatAttrs.append(a + axes)
        else:
            flatAttrs.append(a)
    return flatAttrs


def setAttr(attr, value, ignore_connected=True):
    # is attribute connected?
    if not ignore_connected:
        if mc.listConnections(attr, s=True, d=False):
            mc.warning('attribute.setAttr() -> Attribute "{0}" has incoming connection, skipped!'.format(attr))
            return

    # unlock if locked
    locked = unlockAttr(attr)

    # unlock parent attribute
    parent_attr = unlockAttrParent(attr)

    node, attrName = attr.split('.', 1)

    if ']' in attrName:
        attrType = mc.getAttr(attr, type=True)
    else:
        attrType = mc.attributeQuery(attrName, node=node, at=True)

    if attrType == 'typed':
        attrType = mc.getAttr(attr, type=True)
        if attrType == 'string':
            mc.setAttr(attr, str(value), type=attrType)
        elif attrType == 'stringArray':
            mc.setAttr(attr, len(value), *value, type=attrType)
        else:
            mc.setAttr(attr, value, type=attrType)
    else:
        if not isinstance(value, (list, tuple)):
            value = (value,)
        mc.setAttr(attr, *value)

    # lock again if was locked
    if locked:
        mc.setAttr(attr, lock=True)

    # lock parent attribute again
    if parent_attr:
        mc.setAttr(parent_attr, lock=True)

def getAttrType(attr):
    node, attrName = attr.split('.', 1)
    if ']' in attrName:
        attrType = mc.getAttr(attr, type=True)
    else:
        attrType = mc.attributeQuery(attrName, node=node, at=True)
    if attrType == 'typed':
        attrType = mc.getAttr(attr, type=True)
    return attrType


def unlockAttr(attr):
    """
    unlocks given attr, making sure we can setAttr or connectAttr on it
    :return: attr, if given attribute was locked, otherwise None
    """
    # unlock if locked
    locked = mc.getAttr(attr, lock=True)
    if locked:
        mc.setAttr(attr, lock=False)
        return attr


def unlockAttrParent(attr):
    """
    unlocks given attr's parent, making sure we can setAttr or connectAttr on it
    eg: if node.translateX is locked, then unlocks node.translate and returns node.translate
    :return: parent_attr if it was locked, otherwise None
    """
    node, attrName = attr.split('.', 1)
    if mc.attributeQuery(attrName, node=node, exists=True):
        parent_attr = mc.attributeQuery(attrName, node=node, listParent=True)
        if parent_attr:
            parent_locked = mc.getAttr(node + '.' + parent_attr[0], lock=True)
            if parent_locked:
                mc.setAttr(node + '.' + parent_attr[0], lock=False)
                return node + '.' + parent_attr[0]


def connectAttr(attr1, attr2):
    if not mc.objExists(attr1):
        mc.warning('attribute.connectAttr() -> "{}" does not exist, skipped!'.format(attr1))
        return
    if not mc.objExists(attr2):
        mc.warning('attribute.connectAttr() -> "{}" does not exist, skipped!'.format(attr2))
        return

    # objects can't have two materials, ignore them
    if mc.nodeType(attr2) == 'shadingEngine':
        mc.warning('attribute.connectAttr() -> "{}" is a ShadingEngine node, skipped!'.format(attr2))
        return

    # unlock if locked
    locked = unlockAttr(attr2)

    # unlock parent attribute
    parent_attr = unlockAttrParent(attr2)

    # is attr1 already connected to attr2?
    curConnection = mc.listConnections(attr2, s=True, d=False,
                                       plugs=True, skipConversionNodes=True)
    if curConnection:
        if curConnection[0] == attr1:
            return

    # connect
    mc.connectAttr(attr1, attr2, f=True)

    # lock again if was locked
    if locked:
        mc.setAttr(attr2, lock=True)

    # lock parent attribute again
    if parent_attr:
        mc.setAttr(parent_attr, lock=True)


def addSeparator(node, ln):
    return addAttr(node, ln=ln, at='enum', en=' :', lock=True)


def addStringArray(node, ln, **kwargs):
    return addAttr(node, dt="stringArray", ln=ln, **kwargs)


def addString(node, ln, **kwargs):
    return addAttr(node, dt="string", ln=ln, **kwargs)


def addBool(node, ln, **kwargs):
    return addAttr(node, at="bool", ln=ln, **kwargs)


def addFloat(node, ln, **kwargs):
    return addAttr(node, at="float", ln=ln, **kwargs)


def addInt(node, ln, **kwargs):
    return addAttr(node, at="long", ln=ln, **kwargs)


def addEnum(node, ln, en=[], **kwargs):
    kwargs['en'] = ':'.join(en)
    return addAttr(node, at='enum', ln=ln, **kwargs)


def addAttr(node, force=False, **attrOptions):  # verbose=True,
    """
    given a dict containing settings, re-creates that attribute on node
    :param node:
                node name we want to get it's properties eg: "pCube2"
    :param attrOptions:
                dict containing all the attributes properties. eg: {"min": 0, "max": 1}
    :return:
    """

    # get settings that can't be set on creations and remove them from attrOptions
    # attrName
    if 'longName' in attrOptions:
        longName = attrOptions.pop("longName")
    elif 'ln' in attrOptions:
        longName = attrOptions.pop("ln")
    else:
        longName = 'untitledAttr'

    # exit if attr already exists
    attr = node + '.' + longName
    if mc.attributeQuery(longName, node=node, exists=True):
        if force:
            deleteAttr(attr)
        elif 'verbose' in attrOptions and attrOptions['verbose']:
            mc.warning('Attribute "{0}" already exists, skipped!'.format(attr))
            return attr
        else:
            return attr

    if 'verbose' in attrOptions:
        del attrOptions["verbose"]

    # value
    if 'value' in attrOptions:
        value = attrOptions.pop("value")
    elif 'v' in attrOptions:
        value = attrOptions.pop("v")
    else:
        value = None

    # lock
    if 'lock' in attrOptions:
        lock = attrOptions.pop("lock")
    elif 'l' in attrOptions:
        lock = attrOptions.pop("l")
    else:
        lock = False

    # keyable
    if 'keyable' in attrOptions:
        keyable = attrOptions.pop("keyable")
    elif 'k' in attrOptions:
        keyable = attrOptions.pop("k")
    else:
        keyable = True

    # channelBox
    if 'channelBox' in attrOptions:
        channelBox = attrOptions.pop("channelBox")
    elif 'cb' in attrOptions:
        channelBox = attrOptions.pop("cb")
    else:
        channelBox = True

    # type
    if 'type' in attrOptions:

        if attrOptions['type'] in ('long', 'bool', 'enum', 'double', 'float'):
            attrOptions['at'] = attrOptions.pop("type")
        else:
            attrOptions['dt'] = attrOptions.pop("type")

        if 'attributeType' in attrOptions:
            attrOptions.pop("attributeType")

    # Removes min and maxValue if they are present in the attrOptions dictionary and are a value of None
    if 'maxValue' in attrOptions and attrOptions['maxValue'] is None:
        attrOptions.pop('maxValue')
    if 'minValue' in attrOptions and attrOptions['minValue'] is None:
        attrOptions.pop('minValue')

    # create new attr from given options
    mc.addAttr(node, ln=longName, **attrOptions)

    # set options that can't be set on creations
    if value is not None:
        setAttr(attr, value)
    mc.setAttr(attr, lock=lock)
    mc.setAttr(attr, channelBox=channelBox)
    mc.setAttr(attr, keyable=keyable)

    return attr


def deleteAttr(attr):
    node, longName = attr.split('.', 1)
    if mc.attributeQuery(longName, node=node, exists=True):
        mc.setAttr(attr, lock=False)
        mc.deleteAttr(attr)


def hasAttr(node, attrName):
    if mc.attributeQuery(attrName, node=node, exists=True):
        return True
    return False


def getStringArray(node, attrName):
    v = mc.getAttr(node + '.' + attrName)
    if not v:
        return
    if v.startswith('['):
        return eval(v)


def getUserAttrs(node):
    # attrNames = mc.listAttr(node, userDefined=True, multi=True, scalar=True)
    attrNames = mc.listAttr(node, userDefined=True) or []
    attrs = [node + '.' + x for x in attrNames]
    return attrs


def getAttrInfo(node, attrName):
    """
    gets settings of the given attribute and creates a dict that can be
    passed to mc.addAttr() to recreate a similar attribute.
    :param node:
                node name we want to get it's properties eg: "pCube1"
    :param attrName:
                attribute name we want to get it's properties eg: "stretch"
    :return attrOptions:
                dict containing all the attributes properties. eg: {"min": 0, "max": 1}
    """
    # get attr setting
    attr = node + "." + attrName
    attributeType = mc.attributeQuery(attrName, node=node, at=True)
    niceName = mc.addAttr(attr, q=True, niceName=True)
    keyable = mc.getAttr(attr, keyable=True)
    type_ = mc.getAttr(attr, type=True)
    lock = mc.getAttr(attr, lock=True)
    channelBox = mc.getAttr(attr, channelBox=True)
    value = mc.getAttr(attr)

    # build attribute settings
    attrOptions = {'longName': attrName, 'attributeType': attributeType,
                   'niceName': niceName, 'type': type_,
                   'keyable': keyable, 'lock': lock, 'value': value,
                   'channelBox': channelBox}

    if attributeType == 'enum':
        enumName = mc.addAttr(attr, q=True, enumName=True)
        attrOptions['enumName'] = enumName

    if type_ in ('long', 'int', 'float', 'double'):
        defaultValue = mc.addAttr(attr, q=True, defaultValue=True)
        attrOptions['defaultValue'] = defaultValue
        minValue = mc.addAttr(attr, q=True, minValue=True)
        attrOptions['minValue'] = minValue
        maxValue = mc.addAttr(attr, q=True, maxValue=True)
        attrOptions['maxValue'] = maxValue

    return attrOptions


def promote(source=None, target=None):
    """
    creates input attribute of source on the target
    and connect resulting attribute to the input source attribute.
    useful for when you want an attribute to be controlled by
    an attribute on another control
    @param
        source    string    attribue plug, eg: "main_CTL.stretch"
        target    string    node name, eg: "setting_GRP"
    """
    # attribute to promote
    target_attr = source.split(".")[1]
    duplicateAttr(source, target)
    mc.connectAttr(target + "." + target_attr, source)


def duplicateAttr(source=None, target=None):
    """
    finds second node's user defined attributes
    and adds them to the first node.
    @param
        source    string    attribute plug, eg: "main_CTL.stretch"
        target    string    node name, eg: "setting_GRP"
    """

    # if not (mc.objExists(source) and mc.objExists(target)):
    #     mc.error("Can't duplicate attribute {} to {}!".format(source, target))

    node, attrName = source.split(".")
    attrOptions = getAttrInfo(node, attrName)

    target = target.split('.')[0]
    addAttr(target, **attrOptions)


def transferOutConnections(source=None, target=None, attrs=None, allAttrs=True):
    """
    finds second node's output connections and replaces them
    with your first node.
    useful for places you want to change your contoler but you want
    to keep the connections.

    usage:
        reload(attrLib)
        attrLib.transferOutConnections(source='L_shoulderRsl_JNT', target='L_shoulder_JNT')

    :return:
    """
    if allAttrs:
        outConnections = mc.listConnections(source, s=False, d=True, connections=True, plugs=True) or []
        attrs = []
        for i in range(0, len(outConnections) / 2):
            srcIdx = (i * 2)
            # tgtIdx = (i * 2) + 1
            attrs.append(outConnections[srcIdx].split('.', 1)[-1])
        attrs = list(set(attrs))

    for attr in attrs:
        outputs = mc.listConnections(source + '.' + attr, s=False, d=True, plugs=True) or []
        if not outputs:
            continue
        for out in outputs:
            n, a = out.split('.', 1)
            connectAttr(target + '.' + attr, n + '.' + a)


def transferInConnections(**kwargs):
    source = kwargs.setdefault('source')
    target = kwargs.setdefault('target')

    if not (source and target):
        nodes = mc.ls(sl=True)
        if len(nodes) != 2:
            mc.error('select destination and source nodes.')
        source = nodes[1]
        target = nodes[0]

    # find user defined attributes from source and create them for target
    attrs = mc.listAttr(source, ud=True) or []
    for attr in attrs:
        duplicateAttr(source=source + '.' + attr, target=target)

    sourceIns = mc.listConnections(source, connections=True, destination=False, skipConversionNodes=True,
                                   plugs=True)
    if not sourceIns:
        mc.warning('No attribute to transfer. Skipped!')
        return

    for i in range(len(sourceIns)/2):
        inAttr = sourceIns[(i*2)+1]
        outAttr = sourceIns[(i*2)]

        attrName = outAttr.split('.', 1)[1]

        inAttrName = inAttr.split('.', 1)[1]

        if inAttr != target + '.' + attrName:  # prevent things to connect to themselves

            if mc.nodeType(source) == 'blendShape':
                if (inAttrName != 'outputGeometry') and (inAttrName != 'groupId') and (inAttrName != 'worldMesh[0]'):
                    disconnectAttr(inAttr, outAttr)
                    connectAttr(inAttr, target)
            else:
                disconnectAttr(inAttr, outAttr)
                connectAttr(inAttr, target + '.' + attrName)

        else:
            mc.warning("Can not connect attribute to itself.")


def copySetDrivenKeys(nodes=None):
    """
    What does this do: copies set driven keys to node in the other side
    Notes: finds other node by replacing 'L_' and 'R_', so be careful with the names
    How to use:
    select driven node and run this
    """
    if not nodes:
        nodes = mc.ls(sl=True)
    else:
        nodes = mc.ls(nodes)

    for node in nodes:
        othernode = getMirror(node)

        # for each blend weight that is connected to our node, find all
        # blend weights and it's inputs all the way to driver node
        blendWeightInputs = mc.listConnections(node, type='blendWeighted', skipConversionNodes=True)

        for BWinput in blendWeightInputs:

            # duplicate BWinput
            otherBWinput = mc.duplicate(BWinput)[0]

            # finds targetAttr even if unit conversion exists
            targetAttr = mc.listConnections(BWinput.output, destination=True, source=False, plugs=False)[0]
            if targetAttr.type() == 'unitConversion':
                targetAttr = \
                    mc.listConnections(targetAttr.output, destination=True, source=False, plugs=True)[0].split('.')[
                        -1]
            else:
                targetAttr = \
                    mc.listConnections(BWinput.output, destination=True, source=False, plugs=True)[0].split('.')[-1]

            # finds animCurves
            animCurves = mc.listConnections(BWinput, source=True, destination=False, skipConversionNodes=True,
                                            plugs=False)

            i = 0
            for animCurve in animCurves:

                # duplicate anim curve
                otherAnimCurve = mc.duplicate(animCurve)[0]

                try:  # in case anim curve doesn't have any inputs, no error will occur
                    drivernode = \
                        mc.listConnections(animCurve.input, source=True, destination=False,
                                           skipConversionNodes=True)[0]
                except:
                    mc.warning('Driver node for "%s" not found!' % animCurve)
                    pass

                try:  # in case anim curve doesn't have any inputs, no error will occur
                    driverAttrName = (mc.listConnections(animCurve.input,
                                                         source=True,
                                                         destination=False,
                                                         plugs=True,
                                                         skipConversionNodes=True)[0]).split('.')[-1]
                except:
                    mc.warning('Driver Attribute for "%s" not found!' % animCurve)
                    pass

                otherDriver = getMirror(drivernode)

                # connect input to anim curve
                mc.connect(otherDriver + '.' + driverAttrName, otherAnimCurve.input)
                # connect anim to other blend weight node
                mc.connect(otherAnimCurve.output, otherBWinput.input[i])

                i += 1

            # connect  blend weight node to final attribute
            otherBWinput.output >> othernode + '.' + targetAttr

        # for each animCurve that is connected to our node, find driver attributes
        animCurveInputs = mc.listConnections(node, type='animCurve', skipConversionNodes=True)
        for animCurve in animCurveInputs:
            # duplicate anim curve
            otherAnimCurve = mc.duplicate(animCurve)[0]

            # finds targetAttr even if unit conversion exists
            targetAttr = mc.listConnections(animCurve.output, destination=True, source=False, plugs=False)[0]
            if targetAttr.type() == 'unitConversion':
                targetAttr = mc.listConnections(targetAttr.output,
                                                destination=True,
                                                source=False,
                                                plugs=True)[0].split('.')[-1]
            else:
                targetAttr = mc.listConnections(animCurve.output,
                                                destination=True,
                                                source=False,
                                                plugs=True)[0].split('.')[-1]

            try:  # in case anim curve doesn't have any inputs, no error will occur
                drivernode = mc.listConnections(animCurve.input, source=True,
                                                destination=False, skipConversionNodes=True)[0]
            except:
                mc.warning('Driven node not found!')
                pass

            try:  # in case anim curve doesn't have any inputs, no error will occur
                driverAttrName = (mc.listConnections(animCurve.input, source=True,
                                                     destination=False, plugs=True,
                                                     skipConversionNodes=True)[0]).split('.')[-1]
            except:
                mc.warning('Driven attribute not found!')
                pass

            otherDriver = getMirror(drivernode)

            # connect input to anim curve
            otherDriver + '.' + driverAttrName >> otherAnimCurve.input
            # connect anim to final attribute
            otherAnimCurve.output >> othernode + '.' + targetAttr


def getMirror(node):
    nodeName = node.name()
    if nodeName[:2] == 'L_':
        otherName = node.name().replace('L_', 'R_')
    elif nodeName[:2] == 'R_':
        otherName = node.name().replace('R_', 'L_')
    else:
        otherName = node.name()
    if mc.objExists(otherName):
        othernode = mc.PyNode(otherName)
    else:
        othernode = None
    return othernode


def getNodeNetwork(node, node_data=None, considerOutputs=False, level=1):
    if not node_data:
        node_data = {}

    if level == 0:
        return node_data

    nodeType = mc.nodeType(node)
    node_data[node] = {'type': nodeType, 'connection': {}, 'outConnection': {}}

    changedAttrsAndVals_data = getChangedAttrsAndTheirVals(node)
    node_data[node].update(changedAttrsAndVals_data)

    # find geos and displacement if node is material
    if mc.attributeQuery('outColor', node=node, exists=True):
        SGs = mc.listConnections(node + '.outColor', s=False, d=True) or []
        SGs = [x for x in SGs if mc.nodeType(x) == 'shadingEngine']
        for SG in SGs:
            geos = mc.listConnections(SG + '.dagSetMembers') or []
            if 'geos' not in node_data[node]:
                node_data[node]['geos'] = []
            node_data[node]['geos'].extend(geos)
            disp = mc.listConnections(SG + '.displacementShader')
            if disp:
                node_data[node]['displacementShader'] = disp[0]
                getNodeNetwork(disp[0], node_data)

    # changed attributes
    for attr, v in changedAttrsAndVals_data.items():
        node_data[node][attr] = v

    # attributes with incoming connection
    level -= 1
    ignoreNodesList = ('place2dTexture', 'colorManagementGlobals')

    attr_data = getAttrsWithIncomingConnection(
        node=node,
        ignoreNodesList=ignoreNodesList)
    for attr, inn in attr_data.items():
        node_data[node]['connection'][attr] = inn
        node_data = getNodeNetwork(inn.split('.')[0], node_data, level=level)

    attr_data = getAttrsWithOutgoingConnection(
        node=node,
        ignoreNodesList=ignoreNodesList)
    for attr, inn in attr_data.items():
        node_data[node]['outConnection'][attr] = inn
        node_data = getNodeNetwork(inn.split('.')[0], node_data, level=level)

    return node_data


def getChangedAttrsAndTheirVals(node):
    """
    reload(renderLib)
    print renderLib.getChangedAttrsAndTheirVals(node='remapColor1')

    :param node:
    :return:
    """
    nodeType = mc.nodeType(node)
    nodeRef = mc.createNode(nodeType)
    for attr in mc.listAttr(nodeRef, write=True):
        try:
            mc.getAttr(nodeRef + '.' + attr)
        except:
            continue
    changedAttrsAndValues = compareAttrData(nodeRef, node)
    mc.delete(nodeRef)
    return changedAttrsAndValues


def compareAttrData(nodeRef, node):
    nodeRefData = getAllAttrsAndValues(nodeRef)
    nodeData = getAllAttrsAndValues(node)
    differentData = {}
    for k, v in nodeData.items():
        if k not in nodeRefData:
            differentData[k] = v
        else:
            dv = nodeRefData[k]
            if v != dv:
                differentData[k] = v
    return differentData


def getAllAttrsAndValues(node):
    ignoreAttrList = ['computedFileTextureNamePattern']
    attrsAndValues = {}
    attrs = [x for x in mc.listAttr(node, write=True) if x not in ignoreAttrList]
    flatAttrs = []
    for attr in attrs:
        try:
            isMulti = mc.getAttr(node + '.' + attr, mi=True)
            if isMulti:
                multiAttrs = mc.listAttr(node + '.' + attr, m=True) or []
                if len(multiAttrs) > 1:
                    parentAttrs = multiAttrs[::len(multiAttrs) / len(isMulti)]
                    multiAttrs = [x for x in multiAttrs if x not in parentAttrs]
                    flatAttrs.extend(multiAttrs)
        except:
            continue
        flatAttrs.append(attr)

    for attr in flatAttrs:
        v = getValue(node, attr)
        if v:
            attrsAndValues[attr] = v

    return attrsAndValues


def getValue(node, attr):
    try:
        v = mc.getAttr(node + '.' + attr)
    except:
        return
    if isinstance(v, (list, tuple)):
        if isinstance(v[0], (list, tuple)):
            v = v[0]
    return v


def getAttrsWithIncomingConnection(node, ignoreNodesList=()):
    attrs = mc.listAttr(node, c=True) or []
    connectedAttrs = {}
    for at in attrs:
        if not mc.attributeQuery(at, node=node, exists=True):
            continue
        inputs = mc.listConnections(
            node + '.' + at, c=True, s=True, d=False, plugs=True)
        if inputs:
            for i in range(0, len(inputs), 2):
                innNode, innAttr = inputs[i + 1].split('.', 1)
                subAttr = inputs[i].split('.', 1)[-1]
                if mc.nodeType(innNode) in ignoreNodesList:
                    continue
                connectedAttrs[subAttr] = inputs[i + 1]
    return connectedAttrs


def getAttr(plug, verbose=True):
    node, attr = plug.split('.', 1)
    if mc.attributeQuery(attr, node=node, exists=True):
        return mc.getAttr(plug)
    elif verbose:
        mc.warning('"{}" does not exist!'.format(plug))


def getAttrsWithOutgoingConnection(node, ignoreNodesList=()):
    attrs = mc.listAttr(node, c=True) or []
    connectedAttrs = {}
    for at in attrs:
        if not mc.attributeQuery(at, node=node, exists=True):
            continue
        inputs = mc.listConnections(
            node + '.' + at, c=True, s=False, d=True, plugs=True)
        if inputs:
            for i in range(0, len(inputs), 2):
                innNode, innAttr = inputs[i + 1].split('.', 1)
                subAttr = inputs[i].split('.', 1)[-1]
                if mc.nodeType(innNode) in ignoreNodesList:
                    continue
                connectedAttrs[subAttr] = inputs[i + 1]
    return connectedAttrs


def renameAttr(node, oldAttrName, newAttrName):
    """
    renameAttr(node='scalpShape', oldAttrName='collection1', newAttrName='collection_updo')
    todo: does not work with compound attrs like scalpShape.collection1_right_desc1_Region
    delete them manually first using: mc.deleteAttr('scalpShape.collection1_right_desc1_Region')
    """
    src_sel = om2.MSelectionList()
    src_sel.add(node)
    sel_dep = src_sel.getDependNode(0)
    depFn = om2.MFnDependencyNode(sel_dep)

    attrs = [x for x in mc.listAttr(node) if x.startswith(oldAttrName)]
    for attr in attrs:
        # get old attr's addAttr command
        attrObj = depFn.attribute(attr)
        attrFn = om2.MFnAttribute(attrObj)
        addAttrCmd = attrFn.getAddAttrCmd(longFlags=True)

        # add new attribute
        flags_and_values = addAttrCmd[:-1].split(' -')[1:]
        flags_and_values_dict = {}
        for xy in flags_and_values:
            x, y = xy.split(' ')
            y = y.replace('"', '')
            if x == 'shortName':
                continue
            if x == 'longName':
                y = y.replace(oldAttrName, newAttrName, 1)
            if y == 'true':
                y = True
            if y == 'false':
                y = False
            flags_and_values_dict[str(x)] = y
        if not mc.attributeQuery(flags_and_values_dict['longName'], node=node, exists=True):
            mc.addAttr(node, **flags_and_values_dict)

        # transfer connections
        d_connections = mc.listConnections(node + '.' + attr, plugs=1, d=1, s=0, connections=1) or []
        for i in range(len(d_connections) / 2):
            old_out = d_connections[i * 2]
            new_out = old_out.replace(oldAttrName, newAttrName, 1)
            inn = d_connections[(i * 2) + 1]
            mc.disconnectAttr(old_out, inn)
            mc.connectAttr(new_out, inn, f=1)

        s_connections = mc.listConnections(node + '.' + attr, plugs=1, d=0, s=1, connections=1) or []
        for i in range(len(s_connections) / 2):
            old_inn = s_connections[i * 2]
            new_inn = old_inn.replace(oldAttrName, newAttrName, 1)
            out = s_connections[(i * 2) + 1]
            mc.disconnectAttr(out, old_inn)
            mc.connectAttr(out, new_inn, f=1)

        # delete old attr
        mc.deleteAttr(node + '.' + attr)


def hasInConnection(attr):
    connections = mc.listConnections(attr, s=True, d=False)
    if connections:
        return True
    return False
