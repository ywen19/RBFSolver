import sys
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMaya as OpenMaya
#sys.path.append("/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/")
import numpy as np

nodeName = "RegistrationDeformer"
nodeId = OpenMaya.MTypeId(0x102fff)

vertexIncrement = 0.1

kInput = OpenMayaMPx.cvar.MPxGeometryFilter_input
kInputGeom = OpenMayaMPx.cvar.MPxGeometryFilter_inputGeom
kOutputGeom = OpenMayaMPx.cvar.MPxGeometryFilter_outputGeom
kEnvelope = OpenMayaMPx.cvar.MPxGeometryFilter_envelope


class agingNode(OpenMayaMPx.MPxDeformerNode):
    
    inSrcKeys = OpenMaya.MObject()
    inSrcKey = OpenMaya.MObject()
    inWeights = OpenMaya.MObject()
    inWeight = OpenMaya.MObject()
    inMeshTransM = OpenMaya.MObject()
    
    def __init__(self):
        OpenMayaMPx.MPxDeformerNode.__init__(self)
        
    
    def deform(self, dataBlock, pGeometryIterator, pLocalToWorldMatrix, pGeometryIndex):      
        
        envelopeAttribute = kEnvelope
        envelopeValue = dataBlock.inputValue( envelopeAttribute ).asFloat()

        # Get the input mesh from the datablock using our getDeformerInputGeometry() helper function.     
        inputGeometryObject = self.getDeformerInputGeometry(dataBlock, pGeometryIndex)
        inputGeometryObjectFn = OpenMaya.MFnMesh(inputGeometryObject)
        
        srcKeysListArrayDataHandle = dataBlock.inputArrayValue(agingNode.inSrcKeys)   
        weightsListArrayDataHandle = dataBlock.inputArrayValue(agingNode.inWeights)
        
        #worldTransMdataHandle = dataBlock.inputValue(agingNode.inMeshTransM)
        #worldTransMatrix = worldTransMdataHandle.asMatrix()
        #worldTransM = []
        
        #print worldTransMatrix(0,4)
        
        srcCount = srcKeysListArrayDataHandle.elementCount()
        weightCount = weightsListArrayDataHandle.elementCount()
        
        if (srcCount != weightCount) or (srcCount < 1) or (weightCount < 1):
            return "unknown"
        else:
            srcKeys = np.zeros((srcCount,3), dtype=np.float64)
            weights = np.zeros((weightCount,3), dtype=np.float64)
            
            for i in range(0, srcCount):
                srcKeysListArrayDataHandle.jumpToElement(i)
                srcKeyListDataHandle = srcKeysListArrayDataHandle.inputValue()
                dataHandleSrcKey = srcKeyListDataHandle.child(agingNode.inSrcKey)
                inSrcKey = OpenMaya.MFloatVector()
                inSrcKey = dataHandleSrcKey.asFloatVector()
                for m in range(0,3):
                    srcKeys[i][m] = inSrcKey[m]
                        
            for i in range(0, weightCount):
                weightsListArrayDataHandle.jumpToElement(i)
                weightListDataHandle = weightsListArrayDataHandle.inputValue()
                dataHandleWeight = weightListDataHandle.child(agingNode.inWeight)
                inWeight = OpenMaya.MFloatVector()
                inWeight = dataHandleWeight.asFloatVector() 
                for m in range(0,3):
                    weights[i][m] = inWeight[m]
                        
            origKeyPosM = np.array(srcKeys, dtype=np.float64)
            weightsM = np.array(weights, dtype=np.float64)
            
            minDistList = self.getMinDistList(origKeyPosM)
            
            mPointArray_meshVert = OpenMaya.MPointArray()
            inputGeometryObjectFn.getPoints(mPointArray_meshVert)
            
            mVectorArray = OpenMaya.MPointArray()
            #mVectorArray.setLength(mPointArray_meshVert.length())
            
            for i in range(mPointArray_meshVert.length()):
                origP = [mPointArray_meshVert[i][0], mPointArray_meshVert[i][1], mPointArray_meshVert[i][2]]
                
                deltaMatrixP = np.zeros(origKeyPosM.shape[0], dtype=np.float64)
                for m in range(0, srcCount):
                    a = np.dot( np.subtract(origP, origKeyPosM[m]), np.subtract(origP, origKeyPosM[m]) )
                    powerV = a + np.power(minDistList[m], 2)
                    deltaMatrixP[m] = np.power(powerV, 0.5)
                interpolate = np.dot(deltaMatrixP, weightsM)
                
                result = OpenMaya.MPoint()
                result.x = interpolate[0]
                result.y = interpolate[1]
                result.z = interpolate[2]
                mVectorArray.append(result)
                
            pGeometryIterator.setAllPositions(mVectorArray)
            #inputGeometryObjectFn.setPoints(mVectorArray)
                
                
    def getDeformerInputGeometry(self, dataBlock, pGeometryIndex):
        inputAttribute = OpenMayaMPx.cvar.MPxGeometryFilter_input
        inputGeometryAttribute = OpenMayaMPx.cvar.MPxGeometryFilter_inputGeom
        
        inputHandle = dataBlock.outputArrayValue( inputAttribute )
        inputHandle.jumpToElement( pGeometryIndex )
        inputGeometryObject = inputHandle.outputValue().child( inputGeometryAttribute ).asMeshTransformed()
        
        return inputGeometryObject
    
      
    def getMinDistList(self, srcM):
        minDistList = []
        amount = srcM.shape[0] # = n
        #in case if amount=1, minus an empty array
        if amount>1:
            for i in range(0, amount):
                distBetweenList = []
                for m in range(0, amount):
                    if m!=i:
                        dist = np.linalg.norm(srcM[i]-srcM[m])
                        distBetweenList.append(dist)
                minDist = np.amin(distBetweenList)
                minDistList.append(minDist)
        return minDistList


def deformerCreator():
    nodePtr = OpenMayaMPx.asMPxPtr(agingNode())
    return nodePtr
    

def nodeInitializer():
    mFnCompound = OpenMaya.MFnCompoundAttribute()
    numericAttributeFn = OpenMaya.MFnNumericAttribute()
    matrixattrFn = OpenMaya.MFnMatrixAttribute()

    agingNode.inSrcKeys = mFnCompound.create( 'SrourceKeys', 'srcKeysP')
    agingNode.inSrcKey = numericAttributeFn.create("srcKey", "srcKey", OpenMaya.MFnNumericData.k3Float)
    numericAttributeFn.setKeyable(1)
    numericAttributeFn.setReadable(1)
    mFnCompound.setArray(1)
    mFnCompound.addChild(agingNode.inSrcKey)
    mFnCompound.setReadable(1)
    mFnCompound.setUsesArrayDataBuilder(1)
    agingNode.addAttribute(agingNode.inSrcKeys)
    
    
    agingNode.inWeights = mFnCompound.create("RBFWeights", "RBFws")
    agingNode.inWeight = numericAttributeFn.create("RBFWeight", "RBFw", OpenMaya.MFnNumericData.k3Float)
    numericAttributeFn.setKeyable(1)
    numericAttributeFn.setReadable(1)
    mFnCompound.setArray(1)
    mFnCompound.addChild(agingNode.inWeight)
    mFnCompound.setReadable(1)
    mFnCompound.setUsesArrayDataBuilder(1)
    agingNode.addAttribute(agingNode.inWeights)
    
    '''agingNode.inMeshTransM =  matrixattrFn.create('TransworldMatrix', 'TransworldM')
    matrixattrFn.setKeyable(1)
    matrixattrFn.setReadable(1)
    matrixattrFn.setStorable(1)
    matrixattrFn.setConnectable(1)
    agingNode.addAttribute(agingNode.inMeshTransM)   '''
    
    ''' The input geometry node attribute is already declared in OpenMayaMPx.cvar.MPxGeometryFilter_inputGeom '''

    #==================================
    # OUTPUT NODE ATTRIBUTE(S)
    #==================================
    
    ''' The output geometry node attribute is already declared in OpenMayaMPx.cvar.MPxGeometryFilter_outputGeom '''
    
    #==================================
    # NODE ATTRIBUTE DEPENDENCIES
    #==================================
    # If any of the inputs change, the output mesh will be recomputed.
    
    print dir(OpenMayaMPx.cvar)
    
    agingNode.attributeAffects( agingNode.inSrcKeys, kOutputGeom )
    agingNode.attributeAffects( agingNode.inSrcKey, kOutputGeom )
    agingNode.attributeAffects( agingNode.inWeights, kOutputGeom )
    agingNode.attributeAffects( agingNode.inWeight, kOutputGeom )
    #agingNode.attributeAffects( agingNode.inMeshTransM, kOutputGeom )
    
    OpenMaya.MGlobal.executeCommand("makePaintable -attrType multiFloat -sm deformer AgingDeformer weights;")
    
    
def initializePlugin( mobject ):
    ''' Initialize the plug-in '''
    mplugin = OpenMayaMPx.MFnPlugin( mobject )
    try:
        mplugin.registerNode( nodeName, nodeId, deformerCreator, nodeInitializer, OpenMayaMPx.MPxNode.kDeformerNode )
    except:
        sys.stderr.write( 'Failed to register node: ' + nodeName )
        raise

  
def uninitializePlugin( mobject ):
    ''' Uninitializes the plug-in '''
    mplugin = OpenMayaMPx.MFnPlugin( mobject )
    try:
        mplugin.deregisterNode( nodeId )
    except:
        sys.stderr.write( 'Failed to deregister node: ' + nodeName )
        raise


