import re

import maya.cmds as mc
import maya.OpenMaya as om


def getNS(node=None):
    if node:
        ns = ':'.join(node.split(':')[0:-1])
    else:
        ns = ''
    return ns


def averagePos(poses=None):
    x = y = z = 0.0
    for pos in poses:
        x += pos[0]
        y += pos[1]
        z += pos[2]
    return x / len(poses), y / len(poses), z / len(poses)


def getPoseBetween(objA=None, objB=None, bias=0.5, useSelection=False):
    """
    find Pos Between two objects by a precent and returns a position list
    :param objA: transform node of first object
    :type objA: string (transform name)
    :param objB: transform node of second object
    :type objA: string (transform name)
    :param bias: number beween 0.0 and 1.0 that can be used to get a point
                 closer to given objects. ie: 0.5 means a point exactly
                 between the two, but 0.75 means closer to second transform
    :param useSelection: uses selected objects in Maya as objA and objB
    :return: a list of x, y and z elements. eg: (0, 2, 0)
    """
    if useSelection:
        objA, objB = mc.ls(sl=True)

    vecA = om.MVector(*mc.xform(objA, q=True, t=True, ws=True))
    vecB = om.MVector(*mc.xform(objB, q=True, t=True, ws=True))
    vec = vecB - vecA
    vecNorm = vec.normal()
    length = vec.length()
    vacPartial = vecNorm * bias * length
    finalVec = vacPartial + vecA
    return finalVec[0], finalVec[1], finalVec[2]


def shootRay(objA=None, objB=None, length=0.5):
    vecA = om.MVector(*mc.xform(objA, q=True, t=True, ws=True))
    vecB = om.MVector(*mc.xform(objB, q=True, t=True, ws=True))
    vec = vecB - vecA
    vecNorm = vec.normal()
    vacPartial = vecNorm * length
    finalVec = vacPartial + vecA
    return finalVec[0], finalVec[1], finalVec[2]


def get_matrix(node=""):
    return mc.xform(node, q=True, matrix=True, worldSpace=True)


def setMatrix(node="", matrix=None):
    mc.xform(node, matrix=matrix, worldSpace=True)


def getTransform(node=""):
    """
    :return:
            string    if given node type is transform return itself
                      else if  return it's parent if it's type is transform
                      else error
    """
    if mc.nodeType(node) == "transform":
        return node

    parent = mc.listRelatives(node, p=True, type="transform")
    if parent:
        return parent[0]

    else:
        mc.error('Can\'t find any transform node for "{}"')


def extractHierarchy(from_this="", to_this="", type="transform"):
    """
    returns the hierarchy between (from_this) object and (to_this) object
    :return:
            string[]    list of object's in the hierarchy between two given objects 
    """
    from_hierarchy = getAllChildren(from_this, type, fullPath=True)
    to_hierarchy = getAllParents(to_this, type, fullPath=True)
    from_to_list = [x for x in from_hierarchy if x in to_hierarchy]
    return from_to_list


def getAllParents(node="", type="", includeSelf=True, fullPath=False):
    """
    find all parent of given object if the type matches given type
    :param:  
          node            string    top hierarchy node to search it's parents
          type           string    type of nodes what will get returned
          includeSelf    bool      include the node itself in return list
    :return: 
          string[]    list of object's children
    """
    node = mc.ls(node, long=True)[0]
    all_parents = []
    for i in range(node.count('|')):
        par = node.rsplit('|', i)[0]
        all_parents.append(par)
    all_parents.reverse()

    if not includeSelf:
        if all_parents:
            all_parents.remove(node)

    if type:
        all_parents = [x for x in all_parents if mc.nodeType(x) == type]

    if not fullPath:
        all_parents = [x.split('|')[-1] for x in all_parents]

    return all_parents


def getAllChildren(node="", type="", includeSelf=True, fullPath=False):
    """
    find all children of given object if the type matches given type
    :param:  
          node            string    top hierarchy node to search it's children
          type           string    type of nodes what will get returned
          includeSelf    bool      include the node itself in return list
    :return: 
          string[]    list of object's children
    """
    node = mc.ls(node, long=True)[0]
    all_children = mc.listRelatives(node, ad=True, fullPath=fullPath)
    if includeSelf:
        if all_children:
            if fullPath:
                all_children.append(node)
            else:
                all_children.append(node.split('|')[-1])
        else:
            all_children = [node]
    all_children.reverse()
    if type:
        return [x for x in all_children if mc.nodeType(x) == type]
    else:
        return all_children


def getObjInHierarchy(node="", parent="", fullPath=True):
    """
    search among children of given parent, if node found,
    return it with the full hierarchy path else error.
    :param:  
          parent    string    top hierarchy node to search for node
          node       string    search for this node
    :return: 
          string    full path to node
    """
    children_list = mc.listRelatives(parent, ad=True, fullPath=fullPath)
    for i in range(len(children_list)):
        if children_list[i].endswith(node):
            return children_list[i]
    raise ValueError('"{}" is not a child of "{}".'.format(node, parent))


def parent(child="", par="", update_children=False):
    """
    same as mc.parent but will return full path to child
    :param::
            update_children    boolean    if True, only parents the first node of given list
                                          and updates the list so it hold new nodes' full paths.
    :return:: full path to child
    """

    # parent first node and update children list
    if update_children:

        # check if we have a list
        if not isinstance(child, list):
            raise ValueError('When "update_children" set to True, child must be a list on nodes.')

        children = []

        # check if already is a child of parent
        pars = mc.listRelatives(child[0], parent=True, fullPath=True)
        if pars and pars[0] == par:
            return child

        # parent first node
        first_node = mc.parent(child[0], par)[0]
        first_node = par + "|" + first_node

        # update children's names
        current_path = first_node
        for i in range(1, len(child)):
            current_path = current_path + '|' + child[i]
            children.append(current_path)

        children.insert(0, first_node)
        return children

    # check if already is a child of parent
    pars = mc.listRelatives(child, parent=True, fullPath=True)
    if pars and pars[0] == par:
        return child

    # update_children == False
    # parent node and return full path
    try:
        child = mc.parent(child, par)[0]
        return par + '|' + child
    except:
        mc.warning('Could not parent "{}" under "{}"'.format(child, par))
        return child


def match(node=None, all="", matchTranslate="", matchRotateWith="", matchScale="", t="", r="", s=""):
    """
    :return: None
                match(node, matchTranslate, matchRotateWith, matchScale)
                matches node to target
    """
    if all:
        matchTranslate = matchRotateWith = matchScale = all
    if t:
        matchTranslate = t
    if r:
        matchRotateWith = r
    if s:
        matchScale = s

    if mc.objExists(matchTranslate):
        piv = mc.xform(matchTranslate, q=True, ws=True, rotatePivot=True)
        mc.xform(node, ws=True, t=piv)

    if mc.objExists(matchRotateWith):
        rot = mc.xform(matchRotateWith, q=True, ws=True, rotation=True)
        mc.xform(node, ws=True, rotation=rot)

    if mc.objExists(matchScale):
        scl = mc.xform(matchScale, q=True, ws=True, scale=True)
        mc.xform(node, ws=True, scale=scl)


def setTranslation(node=None, translation=None, space="world"):
    """
    :return: None
                setTranslation(node, translate,space)
                sets world or local position for an object
    """
    if translation is None:
        translation = [0, 0, 0]
    if space == "world":
        mc.xform(node, worldSpace=True, t=translation)
    else:
        mc.xform(node, objectSpace=True, t=translation)


def isShape(node=""):
    """
    :return: True if given node is a shape else False
    :return type: bool
    """
    maya_shapes = ["nurbsCurve", "mesh", "nurbsSurface"]
    if mc.nodeType(node) in maya_shapes:
        return True
    return False


def getShapes(node="", fullPath=False):
    """
    :return: returns all shape of the given node, plus itself if it's a shape too
    :return type: list of strings
    """
    if not mc.objExists(node):  # doesn't exist
        mc.error('"{}" does not exist.'.format(node))

    shape_list = mc.listRelatives(node, children=True, shapes=True, fullPath=True) or []

    # make sure node itself is in the list if it's a shape too
    if isShape(node):
        shape_list.append(node)

    if shape_list and (not fullPath):
        shape_list = [x.split('|')[-1] for x in shape_list]

    return shape_list


def getShapeOfType(node="", nodeType="mesh", fullPath=False):
    """
    :return: string[]
                given node if it's of given type or it's shapes if
                they are of given type, otherwise errors.
    """
    shape_list = []

    all_shapes = getShapes(node=node, fullPath=fullPath)

    for shape in all_shapes:
        if mc.nodeType(shape) == nodeType:
            shape_list.append(shape)

    if shape_list:
        return shape_list

    mc.warning('object "{}" is not of type "{}"'.format(node, nodeType))


def listToHierarchy(node_list=None):
    """
    given a list of objects, parents them and make a hierarchy
    in a way that first object will be parent of all others
    """
    if node_list is None:
        node_list = []
    for i in range(len(node_list) - 1, 0, -1):
        mc.parent(node_list[i], node_list[i - 1])


def getHierarchyByType(node="", type="transform", include_self=True, noIntermediate=True, reverse_list=True):
    """
    :param: include_self: adds input node to the return list
    :return: list of objects of given type under given node's hierarchy
    """
    node_list = []
    children_list = mc.listRelatives(node, ad=True)
    if noIntermediate:
        children_list = mc.ls(children_list, noIntermediate=True)

    if include_self and mc.nodeType(node, type):
        children_list.insert(0, node)

    for child in children_list:
        if mc.nodeType(child) == type:
            node_list.append(child)

    if reverse_list:
        node_list.reverse()

    return node_list


def getParent(node, fullPath=False):
    parentList = mc.listRelatives(node, parent=True, fullPath=fullPath)

    if not parentList:  # no parent found
        return

    if fullPath:  # parent's full path without first '|'
        par = parentList[0][1:]
    else:
        par = parentList[0]

    return par


def getZro(node):
    searchLimit = 0
    while searchLimit < 100:
        node = getParent(node)
        if not node:
            return
        if node.endswith('_ZRO'):
            return node
        searchLimit += 1


def getChild(node, fullPath=False):
    """
    return first found child
    """
    parentList = mc.listRelatives(node, children=True, fullPath=fullPath)

    if not parentList:  # no parent found
        return

    if fullPath:  # parent's full path without first '|'
        par = parentList[0][1:]
    else:
        par = parentList[0]

    return par


def resetTRS(node):
    for x in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
        try:
            mc.setAttr(node + '.' + x, 0)
        except:
            pass

    for x in ['sx', 'sy', 'sz']:
        try:
            mc.setAttr(node + '.' + x, 1)
        except:
            pass


def resetUserAttrs(node):
    attrs = mc.listAttr(node, keyable=True, userDefined=True, unlocked=True, )
    if not attrs:
        return
    for attr in attrs:
        plug = node + '.' + attr
        dv = mc.addAttr(plug, q=True, dv=True)
        mc.setAttr(plug, dv)


def displayOverride(node, task, color=20):
    if task == "on":
        mc.setAttr(node.attr("overrideEnabled"), 1)
    elif task == "off":
        mc.setAttr(node.attr("overrideEnabled"), 0)
    elif task == "col":
        mc.setAttr(node.attr("overrideEnabled"), 1)
        mc.setAttr(node.attr("overrideColor"), color)
    else:
        print 'Select "on" , "off" or "col" with a color name.'


def getDistance(objA=None, objB=None, useSelection=False):
    """
    find distance two objects
    :param objA: transform node of first object
    :type objA: string (transform name)
    :param objB: transform node of second object
    :type objA: string (transform name)
    :param useSelection: uses selected objects in Maya as objA and objB
    :return: distance between given objects as float
    """
    if useSelection:
        objA, objB = mc.ls(sl=True)

    vecA = om.MVector(*mc.xform(objA, q=True, t=True, ws=True))
    vecB = om.MVector(*mc.xform(objB, q=True, t=True, ws=True))
    vec = vecB - vecA
    vecNorm = vec.normal()
    length = vec.length()
    return length


def getDistanceFromPoses(posA=None, posB=None):
    """
    find distance two objects
    :param posA: position of first object
    :type posA: list
    :param posB: position of second object
    :type posB: list
    :param useSelection: uses selected objects in Maya as posA and posB
    :return: distance between given objects as float
    """
    vecA = om.MVector(*posA)
    vecB = om.MVector(*posB)
    vec = vecB - vecA
    vecNorm = vec.normal()
    length = vec.length()
    return length


def mirrorLikeJnt(nodes=None):
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]
    if not nodes:
        nodes = mc.ls(sl=True)
    mirroredObjs = []
    for node in nodes:
        jnt = mc.joint(None)
        match(jnt, node)
        dup = duplicateClean(node)[0]
        mc.parent(dup, jnt)
        mir = mc.mirrorJoint(jnt, mirrorBehavior=True)
        par = mc.listRelatives(node, p=True)
        if par:
            mc.parent(mir[1], par[0])
        else:
            mc.parent(mir[1], world=True)
        mc.delete(mir[0], jnt)
        side = node[0]
        otherSide = 'R' if side == 'L' else 'L'
        mirrorName = node.replace(side, otherSide, 1).split('|')[-1]
        mir = mc.rename(mir[1], mirrorName)
        mirroredObjs.append(mir)

    return mirroredObjs




def mirror_handles(behavior=True):
    """
    mirror control transform values
    """
    sels = mc.ls(sl=True, long=True)

    for ctl in sels:
        otherside = ctl.split('|')[-1].replace('L_', 'R_', 1)
        print(otherside)

        if not mc.objExists(otherside):
            continue
        if behavior:
            temp_loc = mirrorLikeJnt(ctl)
            match(otherside, temp_loc[0])
        else:
            temp_loc = mc.createNode('transform')
            match(temp_loc, ctl)
            mirror(temp_loc)
            match(otherside, temp_loc)

        mc.delete(temp_loc)

    mc.select(sels)

def mirror(target, axis="x", type_="pose", copy=False, children=True, **kwargs):
    """
    Mirror transform nodes

        eg: import transform as trans
            reload(trans)
            trans.mirror('pCube1', axis='x', copy=True, type_='position')

    :param target: Transform node to mirror
    :type target: string

    :param axis: Axis to mirror the transform across. 
                 Valid options are: B{x} or B{y} or B{z}
    :type axis: string

    :param type_: Mirror operation type. Valid options are: position
                  or rotation or pose
    :type type: string

    :param copy: Copies object and mirrors copied 
    :type copy: bool

    :return: Return duplicate target or original target
    :rtype: string
    """
    # duplicate
    if copy:
        target = duplicate(target, hierarchy=True, **kwargs)[0]

    # unParent children so they don't change
    childList = mc.listRelatives(target, children=True, type='transform', fullPath=True)
    tmp_grp = mc.createNode('transform', name='temp_children_bucket')
    if childList:
        mc.parent(childList, tmp_grp)

    # create nodes to calculate other side transformation
    # create final result transform
    trs = mc.createNode('transform', n='trs')
    rslt = mc.createNode('transform', n='rslt')
    rslt = mc.parent(rslt, trs)[0]
    mc.setAttr(rslt + '.ry', 180)

    # create multMatrix
    multMat = mc.createNode('multMatrix')
    mc.connectAttr(target + '.worldMatrix[0]', multMat + '.matrixIn[0]')

    # create fourByFourMatrix
    fourMat = mc.createNode('fourByFourMatrix')
    mc.connectAttr(fourMat + '.output', multMat + '.matrixIn[1]')

    # create decomposeMatrix
    dcmpMat = mc.createNode('decomposeMatrix')
    mc.connectAttr(multMat + '.matrixSum', dcmpMat + '.inputMatrix')

    # connect result
    mc.connectAttr(dcmpMat + '.outputRotate', trs + '.rotate')
    mc.connectAttr(dcmpMat + '.outputTranslate', trs + '.translate')
    mc.connectAttr(target + '.scale', trs + '.scale')

    # set values based on given axis
    if axis == 'x':
        mc.setAttr(fourMat + '.in00', -1)
    elif axis == 'y':
        mc.setAttr(fourMat + '.in11', -1)
    elif axis == 'z':
        mc.setAttr(fourMat + '.in22', -1)
    else:
        mc.error('axis "{0}" is not valid'.format(axis))

    # Now that we have final result we can match target to it
    try:
        mc.parent(rslt, world=True)
    except:
        pass
    match(target, rslt, type_)

    # parent children under their original parent
    if childList:
        tmp_childList = [x.replace(target, tmp_grp) for x in childList]
        mc.parent(tmp_childList, target)

    # Remove extra nodes
    mc.delete(trs, rslt, multMat, fourMat, dcmpMat, tmp_grp)

    # mirror children recursively
    if children:
        if childList:
            for child in childList:
                mirror(child, axis=axis, type_=type_, copy=False, children=True, **kwargs)

    # Return target
    return target


def parentShapes(matchToTransform=False):
    """
    parents first set of selected shapes to the second set of selected transforms
    :param: matchToTransform: if "True" matches the transforms of the curve with the selected objects else it doesn't.
    """
    ctrls = mc.ls(sl=True, allPaths=True)

    half = len(ctrls) / 2

    if matchToTransform:
        for j in range(len(ctrls) / 2):
            shape = mc.listRelatives(ctrls[j], f=True, s=True)
            mc.select(shape, ctrls[half + j])
            mc.parent(add=True, shape=True)
    else:
        for j in range(len(ctrls) / 2):
            newObj = (mc.duplicate(ctrls[j]))[0]
            mc.parent(newObj, ctrls[half + j])
            mc.delete(mc.listRelatives(newObj, f=True, type="transform"))
            mc.makeIdentity(newObj, apply=True, t=1, r=1, s=1)
            mc.parent(newObj, w=True)
            shape = mc.listRelatives(newObj, f=True, s=True)
            mc.select(shape, ctrls[half + j])
            mc.parent(add=True, shape=True)
            mc.delete(newObj)


def unFreeze(nodes=None):
    """
    unFreezes transforms
    """
    if not nodes:
        nodes = mc.ls(sl=True)
    else:
        nodes = mc.ls(nodes)

    if not nodes:
        mc.warning('ehm_tools...UnFreeze: nodes argument needs some object to operate on. No object found!')

    for node in nodes:
        mc.makeIdentity(node, apply=True, t=1, r=1, s=1)
        piv = mc.getAttr(node + ".rotatePivot")[0]
        mc.setAttr(node + ".translate", -piv[0], -piv[1], -piv[2])
        mc.makeIdentity(node, apply=True, t=1, r=1, s=1)
        mc.setAttr(node + ".translate", piv[0], piv[1], piv[2])


def duplicateClean(node, search='', replace='', name=''):
    """
    duplicate a node (usually a transform and shape under it), and removes
    all the garbage that was in the node's hierarchy and was duplicated too,
    except first found shape.

    :param node: node to duplicate (its shape will be duplicated too)
    :type search: string

    :param search: string to search in the input node
    :type search: string
    
    :param replace: string to use in the new objects' names
    :type replace: string

    :return: list containing duplicated object and its shape
    """
    # duplicate the whole hierarchy
    dup = duplicate(node, search=search, replace=replace, hierarchy=True)[0]
    if name:
        dup = mc.rename(dup, name)

    # remove orig shapes
    removeOrigShapes(dup)

    # delete everything under duplicated node, except shape node
    toDel = mc.listRelatives(dup, type='transform', f=True)
    if toDel:
        mc.delete(toDel)

    shapes = getShapes(dup)
    if shapes:  # don't delete found shapes
        shape = shapes[0]
    else:  # return None for shape if shape not found
        shape = None

        # return
    return dup, shape


def removeOrigShapes(node):
    """
    remove all (orig) shapes under given node except the main shape

    :param node: string
        Name of the top node in the hierarchy that you wish to clean
    """
    children = mc.listRelatives(node, ad=True, shapes=True)
    if not children:
        return
    toDeleteShape = [x for x in children if mc.getAttr('%s.intermediateObject' % x)]
    if toDeleteShape:
        mc.delete(toDeleteShape)


def duplicate(node, search='', replace='', hierarchy=False, **kwargs):
    """
    safely duplicate an object. If hierarchy flag in True, renames all the
    children using search and replace strings so there won't be any name
    clashes and if it's False, deletes all the children
    :param node: name of object to be duplicated
    :type node: string
    :param search: string to search in the input node
    :type search: string
    :param replace: string to use in the new objects' names
    :type replace: string
    :param hierarchy: duplicate all the hierarchy or just the parent node
    :type hierarchy: bool
    :return: list of duplicated objects
    """

    # supported types
    supportedTypes = ['joint', 'transform']

    n = node.replace(search, replace, 1)

    # hierarchy False
    if not hierarchy:
        output = mc.duplicate(node, parentOnly=1, returnRootsOnly=1, n=n, **kwargs)
        return output

    # hierarchy True
    objs = mc.duplicate(node, renameChildren=1, n=n, **kwargs)

    origNames = mc.listRelatives(node, ad=True, fullPath=True) or []
    origNames.insert(0, node)
    origNames = [x.split('|')[-1] for x in origNames if mc.nodeType(x) in supportedTypes]

    names = mc.listRelatives(objs[0], ad=True) or []
    names.insert(0, objs[0])
    names = [x for x in names if mc.nodeType(x) in supportedTypes]

    output = []
    for orig, new in zip(origNames, names):
        n = orig.replace(search, replace, 1)
        n = mc.rename(new, n)
        output.append(n)

    return output


def getTRS(node, space='object'):
    """
    gets transform values of given node

    :param node: name of node
    :type node: string
    :return: transform information e.g. [[0,0,0], [0,45,0], [1,1,1]]
    :type return: list
    """
    if space == 'object':
        return [mc.getAttr(node + '.' + at)[0] for at in ('t', 'r', 's')]
    elif space == 'world':
        tmp_node = mc.createNode('transform')
        match(tmp_node, node)
        trs = [mc.getAttr(tmp_node + '.' + at)[0] for at in ('t', 'r', 's')]
        mc.delete(tmp_node)
        return trs


def setTRS(node, trs, space='object'):
    """
    sets transform values on node using given data

    :param node: name of node
    :type node: string
    :param trs: transform information e.g. [[0,0,0], [0,45,0], [1,1,1]]
    :type trs: list
    """
    if space == 'object':
        for i, at in enumerate(['t', 'r', 's']):
            for j, ax in enumerate(['x', 'y', 'z']):
                try:
                    mc.setAttr(node + '.' + at + ax, trs[i][j])
                except:
                    continue
    elif space == 'world':
        tmp_node = mc.createNode('transform')
        for i, at in enumerate(['t', 'r', 's']):
            for j, ax in enumerate(['x', 'y', 'z']):
                mc.setAttr(tmp_node + '.' + at + ax, trs[i][j])
        match(node, tmp_node)
        mc.delete(tmp_node)


def insert(nodes=None, mode='parent', name='offsetGrp', search=None, replace=None):
    """
    :synopsis:
        create a tranform group on node location, either as its parent or child
    :param node: string, name of object that will have offset group on it
    :param mode: parent = new group will be the parent of node
                 child = new node will be the child of node
                 allChilds = new node will be the childe of node, but all other
                             children of node will be parented to this new grp
    :return: :    newly created  offset group
    """
    if not nodes:
        nodes = mc.ls(sl=True)
    if isinstance(nodes, basestring):
        nodes = [nodes]

    ofsGrps = []
    for node in nodes:
        if search and replace:
            name = node.replace(search, replace, 1)
            if name == node:
                name = node + '_GRP'
            if mc.objExists(name):
                mc.warning('object already exists: {}'.format(name))
                continue
        ofs = mc.group(em=True, name=name)
        mc.delete(mc.parentConstraint(node, ofs))

        if mode == 'parent':
            currentParent = getParent(node)
            mc.parent(node, ofs)
            if currentParent:
                mc.parent(ofs, currentParent)

        elif mode == 'child':
            mc.parent(ofs, node)

        elif mode == 'allChilds':
            oldChildren = mc.listRelatives(node, f=True)
            ofs = mc.parent(ofs, node)[0]
            if oldChildren:
                mc.parent(oldChildren, ofs)

        ofsGrps.append(ofs)

    mc.select(ofsGrps)
    return ofsGrps


def attachToMesh(node, mesh):
    """
    node = 'pCube1'
    mesh = 'C_head_GEO'
    transform.attachToMesh(node, mesh)
    """
    surfShape = getShapes(mesh)[0]
    folWorldPos = mc.xform(node, q=True, t=True, ws=True)
    pOnSurf = mc.createNode('closestPointOnMesh')

    mc.connectAttr(surfShape + '.worldMatrix[0]', pOnSurf + '.inputMatrix')
    mc.connectAttr(surfShape + '.worldMesh[0]', pOnSurf + '.inMesh')

    mc.setAttr(pOnSurf + '.inPosition', *folWorldPos)

    uPos = mc.getAttr(pOnSurf + '.result.parameterU')
    vPos = mc.getAttr(pOnSurf + '.result.parameterV')

    cns = mc.pointOnPolyConstraint(mesh, node)[0]

    tgt = mc.pointOnPolyConstraint('pCube1_pointOnPolyConstraint1', q=True, tl=True)[0]
    mc.setAttr('{}.{}U0'.format(cns, tgt), uPos)
    mc.setAttr('{}.{}V0'.format(cns, tgt), vPos)

    mc.delete(pOnSurf)


def isLimited(node, attr):
    return eval('mc.transformLimits("{}", q=True, e{}=True)'.format(node, attr))


def disableLimits(node):
    attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
    for attr in attrs:
        eval('mc.transformLimits("{}", e{}={})'.format(node, attr, [False, False]))


def copyLimits(src, tgt):
    attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
    for attr in attrs:
        # is enabled?
        enabled = eval('mc.transformLimits("{}", q=True, e{}=True)'.format(src, attr))
        eval('mc.transformLimits("{}", e{}={})'.format(tgt, attr, enabled))
        # set limit values
        enabled = eval('mc.transformLimits("{}", q=True, {}=True)'.format(src, attr))
        eval('mc.transformLimits("{}", {}={})'.format(tgt, attr, enabled))


def getGeosUnder(topNode, fullPath=False):
    geos = mc.listRelatives(topNode, ad=True, type='mesh', fullPath=True)
    geos = [mc.listRelatives(x, p=True, fullPath=True)[0] for x in geos]
    geos = list(set(geos))
    if not fullPath:
        geos = [x.split('|')[-1] for x in geos]
    return geos


def matchPivot(driver, driven):
    piv = mc.xform(driver, q=True, ws=True, rp=True)
    mc.xform(driven, ws=True, rp=piv)
    return piv


def rotationFrom3Vectors(vecA, vecB, vecC):
    # transformation matrix
    fmx = mc.createNode('fourByFourMatrix')

    mc.setAttr(fmx + '.in00', vecA[0])
    mc.setAttr(fmx + '.in01', vecA[1])
    mc.setAttr(fmx + '.in02', vecA[2])

    mc.setAttr(fmx + '.in10', vecB[0])
    mc.setAttr(fmx + '.in11', vecB[1])
    mc.setAttr(fmx + '.in12', vecB[2])

    mc.setAttr(fmx + '.in20', vecC[0])
    mc.setAttr(fmx + '.in21', vecC[1])
    mc.setAttr(fmx + '.in22', vecC[2])

    # decompose transformation
    dmx = mc.createNode('decomposeMatrix')
    mc.connectAttr(fmx + '.output', dmx + '.inputMatrix')

    rot = mc.getAttr(dmx + '.outputRotate')[0]

    mc.delete(fmx, dmx)
    return rot


def rotationFrom3Objs(objA, objB, objC, invertX=False, invertZ=False):
    """
    import python.lib.trsLib as trsLib
    reload(trsLib)
    rot =  trsLib.rotationFrom3Objs(objA='a', objB='b', objC='c', invertZ=True)
    mc.setAttr('x.r', *rot)
    """
    vecA = om.MVector(*mc.xform(objA, q=True, t=True, ws=True))
    vecB = om.MVector(*mc.xform(objB, q=True, t=True, ws=True))
    vecC = om.MVector(*mc.xform(objC, q=True, t=True, ws=True))

    vecX = (vecB - vecA).normal()
    if invertX:
        vecX *= -1

    vecZ = (vecA - vecC).normal()
    if invertZ:
        vecZ *= -1

    vecY = (vecX ^ vecZ).normal()
    vecZ = (vecX ^ vecY).normal()

    return rotationFrom3Vectors(vecX, vecY, vecZ)


def getBoundingBox(objs):
    objs = mc.ls(objs)
    objs = list(set([getTransform(x) for x in objs]))
    finalBB = [0, 0, 0, 0, 0, 0]
    for obj in objs:
        bb = mc.xform(obj, q=True, boundingBox=True)
        finalBB[0] = min(finalBB[0], bb[0])
        finalBB[1] = max(finalBB[1], bb[1])
        finalBB[2] = min(finalBB[2], bb[2])
        finalBB[3] = max(finalBB[3], bb[3])
        finalBB[4] = min(finalBB[4], bb[4])
        finalBB[5] = max(finalBB[5], bb[5])
    return finalBB


def getSizeFromBoundingBox(objs):
    bb = getBoundingBox(objs)
    a = bb[1] - bb[0]
    b = bb[3] - bb[2]
    c = bb[5] - bb[4]
    return max(a, b, c)
