import maya.cmds as cmds
import functools as functools


def initModules(src_txt, targ_txt, deformer_txt, rbf_txt, *args):
    #load geometry
    src_geo = cmds.ls(sl=1)
    
    #group for samples
    src_grp = cmds.group(n=src_geo[0]+'_src_sample', empty=True)
    targ_grp = cmds.group(n=src_geo[0]+'_targ_sample', empty=True)
    
    #first pair of space identifier
    src_k1 = cmds.spaceLocator(n='src_'+src_geo[0]+'_01')
    cmds.setAttr(src_k1[0]+'.overrideEnabled', 1)
    cmds.setAttr(src_k1[0]+'.overrideColor', 9)
    targ_k1 = cmds.spaceLocator(n='targ_'+src_geo[0]+'_01')
    cmds.setAttr(targ_k1[0]+'.overrideEnabled', 1)
    cmds.setAttr(targ_k1[0]+'.overrideColor', 14)
    cmds.parent(src_k1[0], src_grp)
    cmds.parent(targ_k1[0], targ_grp)
    
    #registration nodes for deforming
    cmds.select(src_geo[0])
    register_deform = cmds.deformer(type='RegistrationDeformer', n=src_geo[0]+'_register')
    rbf_solver = cmds.createNode('RBFNode', n=src_geo[0]+'_rbf')
    
    #update global
    cmds.textField(deformer_txt, edit=1, text=register_deform[0])
    cmds.textField(rbf_txt, edit=1, text=rbf_solver)
    cmds.textField(src_txt, edit=1, text=src_grp)
    cmds.textField(targ_txt, edit=1, text=targ_grp)
    

def loadModules(module_txt, src_txt, targ_txt, deformer_txt, rbf_txt, *args):
    #read the geometry name for the module going to be loaded
    src_geo = cmds.ls(sl=1)
    cmds.textField(module_txt, edit=1, text=src_geo[0])
    
    cmds.textField(deformer_txt, edit=1, text=src_geo[0]+'_register')
    cmds.textField(rbf_txt, edit=1, text=src_geo[0]+'_rbf')
    cmds.textField(src_txt, edit=1, text=src_geo[0]+'_src_sample')
    cmds.textField(targ_txt, edit=1, text=src_geo[0]+'_targ_sample')
    
   

def addSamples(src_txt, targ_txt, sampleAmount, *args):
    
    src_grp = cmds.textField(src_txt, query=True, text=True)
    targ_grp = cmds.textField(targ_txt, query=True, text=True)
    current_amount = len(cmds.listRelatives(src_grp, children=1))
    print current_amount
    prefix = src_grp[0:-11]
    
    if current_amount<9:
        new_src = cmds.spaceLocator(n='src_'+prefix+'_0'+str(current_amount+1))
        cmds.setAttr(new_src[0]+'.overrideEnabled', 1)
        cmds.setAttr(new_src[0]+'.overrideColor', 9)
        cmds.parent(new_src[0], src_grp)
    
        new_targ = cmds.spaceLocator(n='targ_'+prefix+'_0'+str(current_amount+1))
        cmds.setAttr(new_targ[0]+'.overrideEnabled', 1)
        cmds.setAttr(new_targ[0]+'.overrideColor', 14)
        cmds.parent(new_targ[0], targ_grp)
    
    if current_amount<=99 and current_amount>=9:
        new_src = cmds.spaceLocator(n='src_'+prefix+'_'+str(current_amount+1))
        cmds.setAttr(new_src[0]+'.overrideEnabled', 1)
        cmds.setAttr(new_src[0]+'.overrideColor', 9)
        cmds.parent(new_src[0], src_grp)
    
        new_targ = cmds.spaceLocator(n='targ_'+prefix+'_'+str(current_amount+1))
        cmds.setAttr(new_targ[0]+'.overrideEnabled', 1)
        cmds.setAttr(new_targ[0]+'.overrideColor', 14)
        cmds.parent(new_targ[0], targ_grp)
    

   
def removeSamples(src_txt, targ_txt, *args):
    src_grp = cmds.textField(src_txt, query=True, text=True)
    targ_grp = cmds.textField(targ_txt, query=True, text=True)
    prefix = src_grp[0:-11]
    
    select_key = cmds.ls(sl=1)
    if select_key[0][0]=='s':
        number = select_key[0][-2:]
        cmds.delete(select_key[0])
        cmds.delete('targ_'+prefix+'_'+str(number))
        renameBySize(src_grp, 'src_'+prefix)
        renameBySize(targ_grp, 'targ_'+prefix)
        
    if select_key[0][0]=='t':
        number = select_key[0][-2:]
        cmds.delete(select_key[0])
        cmds.delete('src_'+prefix+'_'+str(number))
        renameBySize(src_grp, 'src_'+prefix)
        renameBySize(targ_grp, 'targ_'+prefix)


def renameBySize(keyGroup, name):
    temp_grp = []
    keys = cmds.listRelatives(keyGroup, children=1)
    amount = len(keys)
    for i in range(1, amount+1):
        temp = cmds.rename(keys[i-1], 'temp_'+str(i))
        temp_grp.append(temp)
        
    for i in range(1, amount+1):
        if i<9:
            cmds.rename(temp_grp[i-1], name+'_0'+str(i))
        if i>=9:
            cmds.rename(temp_grp[i-1], name+'_'+str(i))

    
def registerShape(src_txt, targ_txt, deformer_txt, rbf_txt, *args):
    #get the group
    src_grp = cmds.textField(src_txt, query=True, text=True)
    targ_grp = cmds.textField(targ_txt, query=True, text=True)
    src_lcts = cmds.listRelatives(src_grp, children=True, fullPath=True)
    targ_lcts = cmds.listRelatives(targ_grp, children=True, fullPath=True)
    #get the nodes
    register_node = cmds.textField(deformer_txt, query=True, text=True)
    rbf_node = cmds.textField(rbf_txt, query=True, text=True)
    
    amount = len(src_lcts)
    srcDecopmpMList = []
    for i in range(0, amount):
        srcDecompose = cmds.createNode("decomposeMatrix")
        srcDecopmpMList.append(srcDecompose)
        targDecompose = cmds.createNode("decomposeMatrix")
        
        cmds.connectAttr(src_lcts[i]+'.worldMatrix[0]', srcDecompose+'.inputMatrix')
        cmds.connectAttr(srcDecompose+'.outputTranslate', rbf_node+'.SrourceKeys['+str(i)+'].srcKey')
        
        cmds.connectAttr(targ_lcts[i]+'.worldMatrix[0]', targDecompose+'.inputMatrix')
        cmds.connectAttr(targDecompose+'.outputTranslate', rbf_node+'.TargetKeys['+str(i)+'].targKey')
    cmds.setAttr(rbf_node+'.Solve', 1)
    
    for i in range(0, amount):
        cmds.connectAttr(srcDecopmpMList[i]+'.outputTranslate', register_node+'.SrourceKeys['+str(i)+'].srcKey')
        cmds.connectAttr(rbf_node+'.Weights['+str(i)+']weight', register_node+'.RBFWeights['+str(i)+'].RBFWeight')
    #cmds.setAttr(rbf_node+'.Solve', 0)

    

def deleteAll(src_txt, targ_txt, deformer_txt, rbf_txt, *args):
    rbf_node = cmds.textField(rbf_txt, query=True, text=True)
    register_node = cmds.textField(deformer_txt, query=True, text=True)
    #income_rbf = cmds.listConnections(rbf_node)
    #for element in income_rbf:
    #    cmds.delete(element)
    cmds.delete(rbf_node)
    cmds.delete(register_node)
    src_grp = cmds.textField(src_txt, query=True, text=True)
    targ_grp = cmds.textField(targ_txt, query=True, text=True)
    cmds.delete(src_grp)
    cmds.delete(targ_grp)
        


def shapeRegister():
    
    windowID = "ShapeRegister"
    if cmds.window(windowID,exists=True):
        cmds.deleteUI(windowID)
    mywindow = cmds.window(windowID, title="Shape Registration", w=100)
    cmds.columnLayout(adjustableColumn=True)
    
    #for storing nodes
    deformer_txt = cmds.textField(vis=0)
    rbf_txt = cmds.textField(vis=0)
    src_txt = cmds.textField(vis=0)
    targ_txt = cmds.textField(vis=0)
    cmds.textField(src_txt, edit=1, text='src_sample')
    cmds.textField(targ_txt, edit=1, text='targ_sample')
    cmds.text("Module", align='center')
    module_txt = cmds.textField(vis=1)
    
    cmds.button(label="Load Mesh", h=30, backgroundColor=(0.92,0.84,0.21), command = functools.partial(initModules, src_txt, targ_txt, deformer_txt, rbf_txt))
    cmds.button(label='Load Module', h=30, backgroundColor=(0.92,0.84,0.21), command = functools.partial(loadModules, module_txt, src_txt, targ_txt, deformer_txt, rbf_txt))
    
    
    
    #sample points
    cmds.separator(height=20, style='double')
    cmds.text("samples", align='center')
    
    cmds.button(label="+", h=30, backgroundColor=(0.92,0.63,0.21), command = functools.partial(addSamples, src_txt, targ_txt))
    cmds.button(label="-", h=30, backgroundColor=(0.92,0.63,0.21), command = functools.partial(removeSamples, src_txt, targ_txt))
    
    #reconnect
    #cmds.button(label = "Reconnect", h=30, backgroundColor=(0.7,0.94,0.95), command = functools.partial(reconnectNodes, src_txt, targ_txt, deformer_txt, rbf_txt))
    
    #register
    cmds.separator(height=30, style='double')
    cmds.button(label = "Register", h=30, backgroundColor=(0.51,0.93,0.4), command = functools.partial(registerShape, src_txt, targ_txt, deformer_txt, rbf_txt))
    
    #delete whole module system
    cmds.separator(height=30, style='double')
    cmds.button(label = "Delete All", h=30, backgroundColor=(0.95,0.47,0.47), command = functools.partial(deleteAll, src_txt, targ_txt, deformer_txt, rbf_txt))
    
    cmds.showWindow()
    

if __name__ == "__main__" :
    shapeRegister()