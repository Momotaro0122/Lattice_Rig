# maya modules
import maya.cmds as mc

# iRig modules
from lib import control
from lib import trsLib
from lib import attrLib


def launch():
    result = mc.promptDialog(
        title='Lattice Rig',
        message='Select Geo and Enter Lattice Name:',
        button=['OK', 'Cancel'],
        defaultButton='OK',
        cancelButton='Cancel',
        dismissString='Cancel',
        text='C_Body'
    )

    if result == 'OK':
        prefix = mc.promptDialog(query=True, text=True)
    else:
        return
    build_lat_rig(lat_name=prefix)


def build_lat_rig(lat_name="C_Body"):
    if not mc.ls(selection=True):
        mc.warning("Please select one or more pieces of Geometry before trying again")
        return

    # create the lattice
    ffd_node, ffd_lattice, ffd_base = mc.lattice(
        divisions=(3, 3, 3),
        objectCentered=True,
        outsideLattice=1
    )
    ffd_node = mc.rename(ffd_node, lat_name + '_Lattice_Node')
    ffd_lattice = mc.rename(ffd_lattice, lat_name + '_Lattice_Cage')
    ffd_base = mc.rename(ffd_base, lat_name + '_Lattice_Base')
    latticeUtil_Grp = mc.group(ffd_lattice, ffd_base, name=lat_name + "_Lattice_Util_Grp")

    # get top mid and bottom rows
    upr_lat_point = mc.ls(ffd_lattice + ".pt[0:2][2][0:2]", flatten=True)
    mid_lat_point = mc.ls(ffd_lattice + ".pt[0:2][1][0:2]", flatten=True)
    lwr_lat_point = mc.ls(ffd_lattice + ".pt[0:2][0][0:2]", flatten=True)

    # create clusters
    clusters = []
    for i, point in enumerate(upr_lat_point):
        cls = mc.cluster(point, n="{}_Lattice_Upr_{:02d}_Cls".format(lat_name, i + 1))[-1]
        clusters.append(cls)
    for i, point in enumerate(mid_lat_point):
        cls = mc.cluster(point, n="{}_Lattice_Mid_{:02d}_Cls".format(lat_name, i + 1))[-1]
        clusters.append(cls)
    for i, point in enumerate(lwr_lat_point):
        cls = mc.cluster(point, n="{}_Lattice_Lwr_{:02d}_Cls".format(lat_name, i + 1))[-1]
        clusters.append(cls)

    # calculate size
    bb = mc.xform(ffd_lattice, bb=True, q=True)
    size = bb[3] - bb[0]

    # find row centers
    upr_row_poses = [mc.xform(x, q=True, ws=True, t=True) for x in upr_lat_point]
    mid_row_poses = [mc.xform(x, q=True, ws=True, t=True) for x in mid_lat_point]
    lwr_row_poses = [mc.xform(x, q=True, ws=True, t=True) for x in lwr_lat_point]
    upr_row_center = trsLib.averagePos(upr_row_poses)
    mid_row_center = trsLib.averagePos(mid_row_poses)
    lwr_row_center = trsLib.averagePos(lwr_row_poses)

    # create master control
    side = lat_name[0]
    if side not in ['L', 'C', 'R']:
        side = 'C'
    descriptor = lat_name[2:] + '_Lattice_Base'
    base_ctl = control.Control(
        side=side,
        descriptor=descriptor,
        offsetName='Offset_Grp',
        translate=mid_row_center,
        color='greyDark',
        shape='cube',
        size=size * 1.1
    )
    base_ctl_grp = base_ctl.ofs
    base_ctl = base_ctl.name
    mc.parentConstraint(base_ctl, ffd_base, mo=True)
    mc.scaleConstraint(base_ctl, ffd_base, mo=True)

    # create main control
    descriptor = lat_name[2:] + '_Lattice_Main'
    ctl = control.Control(
        side=side,
        descriptor=descriptor,
        offsetName='Offset_Grp',
        parent=base_ctl,
        translate=mid_row_center,
        shape='cube',
        size=size * 1.05
    )
    main_ctl = ctl.name

    # create main controls
    main_ctls = {}
    for upr_mid_lwr, center in zip(
            ['Upr', 'Mid', 'Lwr'],
            [upr_row_center, mid_row_center, lwr_row_center]):
        descriptor = lat_name[2:] + '_' + upr_mid_lwr
        ctl = control.Control(
            side=side,
            descriptor=descriptor,
            offsetName='Offset_Grp',
            parent=main_ctl,
            translate=center,
            shape='square',
            size=size * 1.0
        )
        main_ctls[upr_mid_lwr] = ctl.name

    # create sub controls
    for cls in clusters:
        # find the row name
        upr_mid_lwr = 'Upr'
        if cls.startswith(lat_name + '_Lattice_Mid'):
            upr_mid_lwr = 'Mid'
        elif cls.startswith(lat_name + '_Lattice_Lwr'):
            upr_mid_lwr = 'Lwr'

        # find side and descriptor names
        side = cls[0]
        descriptor = cls[2:].replace('_ClsHandle', '')

        # create the sub controls
        ctl = control.Control(
            side=side,
            descriptor='{}'.format(descriptor),
            offsetName='Offset_Grp',
            parent=main_ctls[upr_mid_lwr],
            matchTranslate=cls,
            lockHideAttrs=['r', 's', 'v'],
            shape='cube',
            useSecondaryColors=True,
            size=size * 0.2
        )
        mc.parent(cls, ctl.name)
        mc.setAttr(cls + ".v", 0)

    # add outsideLattice attributes to control
    outside_at = attrLib.addEnum(
        base_ctl,
        'outsideLattice',
        en=['Inside', 'All', 'Falloff']
    )
    mc.connectAttr(outside_at, ffd_node + '.outsideLattice')

    # add outsideFalloffDist attributes to control
    outside_falloff_at = attrLib.addFloat(
        base_ctl,
        'outsideFalloffDist',
        min=0
    )
    mc.connectAttr(outside_falloff_at, ffd_node + '.outsideFalloffDist')

    # add envelope attributes to control
    envelope_at = attrLib.addFloat(
        base_ctl,
        'envelope',
        min=0,
        max=1,
        dv=1
    )
    mc.connectAttr(envelope_at, ffd_node + '.envelope')

    # connect visibility
    if mc.objExists('Control_Ctrl'):
        vis_attr = attrLib.addEnum('Control_Ctrl', (lat_name + '_LatticeVis'), en=['Hide', 'Show'])
        mc.connectAttr(vis_attr, base_ctl_grp + '.v')

    # Parent Util group into rig, if present
    if mc.objExists("Utility_Grp"):
        mc.parent(latticeUtil_Grp, "Utility_Grp")
    else:
        print("The standard rig template groups are not present in the scene. Please parent the lattice manually.")
