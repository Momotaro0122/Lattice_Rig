import os

import maya.cmds as mc

import crvLib
import display
import trsLib
import renameLib
import attrLib


COLORS = {'C': 'yellow',
          'L': 'blue',
          'R': 'red'}

SECCOLORS = {'C': 'brown',
             'L': 'cyan',
             'R': 'pink'}


class Control(object):
    """
    class for creating control objects
    """

    def __init__(self,
                 descriptor="new",
                 side=None,
                 parent=None,
                 createOffsetGrp=True,
                 shape="circle",
                 size=1.0,
                 scale=(1, 1, 1),
                 orient=(0, 1, 0),
                 moveShape=(0, 0, 0),
                 rotateShape=(0, 0, 0),
                 translate=None,
                 rotate=None,
                 matchTranslate="",
                 matchRotate="",
                 matchScale="",
                 trs=((0, 0, 0), (0, 0, 0), (1, 1, 1)),
                 color=None,
                 useSecondaryColors=False,
                 suffix="Ctrl",
                 lockHideAttrs=['v'],
                 offsetName='Offset_Grp',
                 gimbal=False,
                 new_style_ofs=False,
                 verbose=False):

        self.verbose = verbose
        self.side = side
        self.suffix = suffix
        self.offsetName = offsetName
        if side:
            self._name = self.side + "_" + descriptor + "_" + self.suffix
        else:
            self._name = descriptor + "_" + self.suffix
        self.fullName = self._name  # eg: "|rig_GRP|control_GRP|mainOffset_GRP|C_new_CTL"
        self.parent = parent
        self.scale = [scale[0] * size, scale[1] * size, scale[2] * size]
        self.orient = orient
        self.moveShape = moveShape
        self.rotateShape = rotateShape
        self.crv_shape = shape
        self.ofs = ""
        self.ofsFullName = ""
        self.createOffsetGrp = createOffsetGrp
        self.matchTranslate = matchTranslate
        self.matchRotate = matchRotate
        self.matchScale = matchScale
        self.translate = translate
        self.rotate = rotate
        self.trs = trs
        self.color = color
        self.new_style_ofs = new_style_ofs

        # guess color from side if color is not given by user
        if not self.color:
            if useSecondaryColors:
                self.color = SECCOLORS[self.side or 'C']
            else:
                self.color = COLORS[self.side or 'C']

        # create control
        self.name, self.shapes = self.create()

        # set color
        display.setColor(self.shapes, self.color)

        # lock and hide attrs
        attrLib.lockHideAttrs(self.fullName, attrs=lockHideAttrs)

        self.gimbal_ctl = None
        if gimbal:
            self.gimbal_ctl = Control(
                 descriptor=descriptor + '_Gimbal',
                 side=side,
                 parent=self.name,
                 createOffsetGrp=createOffsetGrp,
                 shape=self.crv_shape,
                 size=size * 0.9,
                 scale=scale,
                 orient=orient,
                 moveShape=moveShape,
                 rotateShape=rotateShape,
                 translate=translate,
                 rotate=rotate,
                 matchTranslate=matchTranslate,
                 matchRotate=matchRotate,
                 matchScale=matchScale,
                 trs=trs,
                 color=color,
                 useSecondaryColors=useSecondaryColors,
                 suffix=suffix,
                 lockHideAttrs=lockHideAttrs,
                 offsetName=offsetName,
                 gimbal=False,
                 new_style_ofs=new_style_ofs,
                 verbose=verbose)
            vis_at = attrLib.addInt(
                self.name,
                'GimbalVis',
                min=0,
                max=1,
                keyable=False
            )
            for shape in self.gimbal_ctl.shapes:
                mc.connectAttr(vis_at, shape + '.v')

    @staticmethod
    def exportCtls(path):
        """
        export all controls from current scene

        usage:
            filePath = "C:/Users/Ehsan/Desktop/ctls.ma"
            control.Control.exportCtls(filePath)
        """
        # get all controls in the scene
        ctls = mc.ls('*_CTL', '*_Ctl', '*_ctl', '*_CTRL', '*_Ctrl', '*_ctrl', long=True)

        # group all new controls
        grp = mc.createNode('transform', n='control_GRP_temp')

        # tmpCtls = []
        for ctl in ctls:
            # if curve shape has incoming connection, break it
            shapes = crvLib.getShapes(ctl, fullPath=True) or []
            mc.delete(shapes, ch=True)

            # transfer colors from shapes to transforms
            # useful for older system where shape have colors instead of trasnform
            display.transfer_color_from_shape_to_transform(ctl)

            # duplicate control
            tmpCtl = mc.duplicate(ctl, name=ctl.split('|')[-1] + '_temp')[0]

            # delete non shape children
            all_children = mc.listRelatives(tmpCtl, fullPath=True) or []
            crv_shape_children = crvLib.getShapes(tmpCtl, fullPath=True) or []
            [mc.delete(x) for x in all_children if x not in crv_shape_children]

            # add _temp to end of shape names
            ctl_shapes = crvLib.getShapes(ctl, fullPath=True) or []
            tmpCtl_shapes = crvLib.getShapes(tmpCtl, fullPath=True) or []
            for s, tmpS in zip(ctl_shapes, tmpCtl_shapes):
                mc.rename(tmpS, s.split('|')[-1] + '_temp')

            #
            attrLib.unlock(tmpCtl, ['t', 'r', 's'])
            mc.parent(tmpCtl, grp)

            # delete children under duplicated controls
            children = mc.listRelatives(tmpCtl, ad=True, fullPath=True, type="nurbsCurve") or []
            for child in children:
                if not mc.nodeType(child) == 'nurbsCurve':
                    try:
                        mc.delete(child)
                    except:
                        pass

        # export all temp controls
        mc.select(grp)
        mc.file(path, f=True, op="v=0;", typ="mayaAscii", es=True)

        mc.delete(grp)
        print('Controls exported successfully!')

    @staticmethod
    def importCtls(path):
        """
        import all controls from current scene
        
        usage:
            filePath = "C:/Users/Ehsan/Desktop/ctls.ma"
            control.Control.importCtls(filePath)
        """
        if not os.path.isfile(path):
            mc.warning('Control shape file "{0}" can not be found, skipped!'.format(path))
            return

        mc.file(path, i=True)
        newCrvsShapes = mc.listRelatives('control_GRP_temp', ad=True, type='nurbsCurve', fullPath=True) or []
        newCrvs = list(set([mc.listRelatives(x, p=True)[0] for x in newCrvsShapes]))

        for newCrv in newCrvs:
            # find old crv
            oldCrv = newCrv.split('|')[-1].replace('_temp', '')
            if not mc.objExists(oldCrv):
                mc.warning('Control "{0}" does not exist , skipped!'.format(oldCrv))
                continue

            # use RGB of curve, if not found, use RGB of curve shapes
            crvShapes = trsLib.getShapes(newCrv, fullPath=True) or []
            crvColor = display.getColor(newCrv)
            if crvColor == 'noColor':
                crvColor = 'noColor'
                # Look for colors from all nodes, starting from shapes, then back up to transform
                for color_candidate in crvShapes + [newCrv]:
                    crvColor = display.getColor(color_candidate)
                    if crvColor != 'noColor':
                        break

            # Turn on override on transform to follow how framework handles colors
            mc.setAttr('{0}.overrideEnabled'.format(newCrv), 1)
            display.setColor(newCrv, color=crvColor)

            for crvShape in crvShapes:
                # Set index colouring of shape nodes back to noColor
                mc.setAttr(crvShape + ".overrideColor", 0)

                # Turn off override on shapes to follow how framework handles colors
                mc.setAttr('{0}.overrideEnabled'.format(crvShape), 0)

            crvLib.copyShape(newCrv, oldCrv)

        mc.delete('control_GRP_temp')

        print('Controls imported successfully!')

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value == self._name:
            return
        unique_name = renameLib.getUniqueName(value)
        self.n = value
        self._rename(unique_name)

    def _getUniqueName(self, value):
        return renameLib.getUniqueName(value)

    def _rename(self, value):
        mc.rename(self.fullName, value)  # rename ctl
        self.fullName = self.fullName.replace(self._name, value)  # update ctl.fullName
        self._name = value  # update ctl.name
        if mc.objExists(self.ofsFullName):
            ofs_new_name = value + '_' + self.offsetName
            mc.rename(self.ofsFullName, ofs_new_name)  # rename ofs
            self.ofsFullName = self.ofsFullName.replace(self.ofs, ofs_new_name)
            self.ofs = ofs_new_name  # update ctl.ofs

    def setParent(self, par=""):
        """
        keeps ofsFullName and fullName up to date after re parenting
        """

        if par == "world":
            if not trsLib.getParent(self.ofs):  # already under world
                return
            mc.parent(self.ofs, world=True)
            self.ofsFullName = self.ofs
            self.fullName = self.ofsFullName + "|" + self.name
            self.parent = ''

        if mc.objExists(par):
            parent_fullName = mc.ls(par, long=True)[0][1:]  # remove first "|" to make the fullNames more flexible
            curPar = trsLib.getParent(self.ofs, fullPath=True)
            if curPar == parent_fullName:  # already under given parent
                return
            mc.parent(self.ofs, parent_fullName)
            self.ofsFullName = parent_fullName + "|" + self.ofs
            self.fullName = self.ofsFullName + "|" + self.name
            self.parent = parent_fullName

        else:
            mc.error('Given parent "{0}" does not exist!'.format(par))

    def setCtlParent(self, parent=""):
        """
        keeps fullName up to date after re parenting
        """
        if mc.objExists(parent):
            parent_fullName = mc.ls(parent, long=True)[0]
            par = mc.listRelatives(self.fullName, parent=True, fullPath=True)
            if par and par[0] == parent_fullName:
                return
            mc.parent(self.fullName, parent_fullName)
            self.fullName = parent_fullName + "|" + self.name

    def addOfsGrp(self, new_style=False):
        """
        create offset group
        :param new_style: will replace _Ctrl with _Ofs instead of adding _Offset_Grp to the end
        """
        if new_style:
            n = self.name.replace('_Ctrl', '_Ofs')
        else:
            n = self.name + '_' + self.offsetName
        self.ofs = mc.group(empty=True, name=n)
        self.ofsFullName = "|" + self.ofs
        trsLib.match(self.ofs, all=self.fullName)
        self.setCtlParent(self.ofs)

        if self.parent:
            self.setParent(self.parent)

    def create(self):
        """
        create control with given settings
        returns transform and shape of newly created control
        """
        if self.verbose:
            print('\t\t\tCreating "{}" control'.format(self.name))

        if not mc.objExists(self._name):
            trans, shapes = crvLib.create(
                shape=self.crv_shape,
                name=self._name,
                scale=self.scale,
                orient=self.orient,
                move=self.moveShape,
                rotate=self.rotateShape
            )

            # match pose (first trs, then match, then translate - usually only one is enough)
            if self.trs:
                trsLib.setTRS(self.name, self.trs)

            trsLib.match(self.name,
                         t=self.matchTranslate,
                         r=self.matchRotate,
                         s=self.matchScale)
            if self.translate:
                trsLib.setTranslation(self.name, translation=self.translate)
            if self.rotate:
                mc.xform(self.name, worldSpace=True, ro=self.rotate)

            # offset group
            if self.createOffsetGrp:
                self.addOfsGrp(new_style=self.new_style_ofs)

            # make rotate order keyable and visible in channelbox
            attrLib.lockHideAttrs(self._name, ['rotateOrder'], lock=0, hide=0)
        else:
            trans = self._name
            shapes = trsLib.getShapes(self._name)
            mc.warning('"{0}" already exists, skipped!'.format(self._name))

        return trans, shapes


def setBorderSize():
    nodes = mc.ls(sl=True)
    for node in nodes:
        line = node + '_Border'
        mc.move(1, 0, 0, line + '.cv[0]', r=True, os=True)
        mc.move(1, 0, 0, line + '.cv[1]', r=True, os=True)
        mc.move(1, 0, 0, line + '.cv[5]', r=True, os=True)
