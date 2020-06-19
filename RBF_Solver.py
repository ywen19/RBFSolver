import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import sys
#sys.path.append("/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/")
import numpy as np

nodeName = "RBFNode"
nodeId = OpenMaya.MTypeId(0x87014)

class RBFNode(OpenMayaMPx.MPxNode):
    
    inSrcKeys = OpenMaya.MObject()
    inSrcKey = OpenMaya.MObject()
    inTargKeys = OpenMaya.MObject()
    inTargKey = OpenMaya.MObject()
    
    inSwitch = OpenMaya.MObject() #once on, solve RBF
    
    outWeights = OpenMaya.MObject()
    outWeight = OpenMaya.MObject()
       

    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)
    
    #function define for solving RBF
    
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
        #print len(minDistList)
        return minDistList
        
    def getInterpolateMatrixH(self, srcM, minDistList):
        amount = srcM.shape[0]
        HList = []
        if amount>1:
            for i in range(0, amount):
                for m in range(0, amount):
                    distBetween = np.linalg.norm(srcM[i]-srcM[m])
                    sum = distBetween**2 + minDistList[m]**2
                    value = sum**0.5
                    
                    HList.append(value)
            
        H = np.array(HList)
        H = np.reshape(H, (amount, amount))
        return H
        
    def getEigens(self, H):
        HTranspose = H.transpose()
        HMultHtranspose = np.dot(H, HTranspose)
    
        eigens = np.linalg.eig(HMultHtranspose)
        return eigens

    def getTargProjToEigenZ(self, targM, eigenVectors):
        targMTranspose = targM.transpose() #3*25 ---> 3*n
        Z = np.dot(targMTranspose, eigenVectors)
        return Z
        
    def getEta(self, eigenValues, lambdaV):
        # func(6)
        eta = 0
        amount =  eigenValues.shape[0] #(25,) ---> n*1
        for i in range(0, amount):
            numerator = eigenValues[i]
            denominator = (eigenValues[i]+lambdaV) ** 2
            eta += (numerator/denominator)
        return eta
        
    def getErrorVTransMultErrorV(self, lambdaV, Z, eigenValues):
        # func(7)
        #print Z.shape (Z not sep)  (3,25) ---> 3*n
        #print Z[0].shape #(25, )
        #print Z[:,0].shape #(3, )    
        result = 0
        amount =  eigenValues.shape[0] #(25,) ---> n*1
        for i in range(0, amount):
            numerator = (lambdaV**2) * (np.dot(Z[:,i], Z[:,i]))
            denominator = (eigenValues[i] + lambdaV)**2
            result += (numerator/denominator)
        return result
        
    def getWeightTransAWeight(self, eigenValues, Z, lambdaV):
        # func(8)
        result = 0
        amount = eigenValues.shape[0] #(25,) ---> n*1
        for i in range(0, amount):
            numerator = eigenValues[i] * (np.dot(Z[:,i], Z[:,i]))
            denominator = (eigenValues[i] + lambdaV)**3
            result += (numerator/denominator)
        return result
        
    def getNMinusGamma(self, lambdaV, eigenValues):
        # func(9)
        result = 0
        amount = eigenValues.shape[0] #(25,) ---> n*1
        for i in range(0, amount):
            numerator = lambdaV
            denominator = eigenValues[i] + lambdaV
            result += (numerator/denominator)
        return result
        
    def getGCV(self, lambdaV, Z, eigenValues):
        n = eigenValues.shape[0] #(25,) ---> n*1
        numerator = n * self.getErrorVTransMultErrorV(lambdaV, Z, eigenValues)

        denominator = (self.getNMinusGamma(lambdaV, eigenValues)) ** 2
        GCV = numerator/denominator
        return GCV
        
    def getLambdaV(self, eigenValues, lambdaV, Z):
        part1_numerator = self.getEta(eigenValues, lambdaV)
        part1_denominator = self.getNMinusGamma(lambdaV, eigenValues)
        part1 = part1_numerator/part1_denominator
        
        part2_numerator = self.getErrorVTransMultErrorV(lambdaV, Z, eigenValues)
        part2_denominator = self.getWeightTransAWeight(eigenValues, Z, lambdaV)
        part2 = part2_numerator/part2_denominator
    
        lambdaV = part1 * part2
        return lambdaV
        
    def calWeight(self, H, lambdaV, targM):
        amount = H.shape[0] #25
        HTranspose = H.transpose()
        I = np.identity(amount, dtype=np.float64)
        A = np.dot(HTranspose, H) + (lambdaV*I) #(25,25) ---> n*n
        AInvMultHTrans = np.dot(np.linalg.inv(A), HTranspose) #(25,25) ---> n*n
        weight = np.dot(AInvMultHTrans, targM) #(25,25)*(25,3) ---> (25,3)
        return weight
    
    def compute(self, plug, dataBlock):
        if (plug==RBFNode.outWeights)or(plug.parent()==RBFNode.outWeights):
            #sys.stderr.write("compute... \n")
            switchDataHandle = dataBlock.inputValue(RBFNode.inSwitch)
            inSwitchVal = switchDataHandle.asBool()
            
            srcKeysListArrayDataHandle = dataBlock.inputArrayValue(RBFNode.inSrcKeys)
            
            targKeysListArrayDataHandle = dataBlock.inputArrayValue(RBFNode.inTargKeys)
            
            srcCount = srcKeysListArrayDataHandle.elementCount()
            targCount = targKeysListArrayDataHandle.elementCount()
            
            outWeightsListArrayDataHandle = dataBlock.outputArrayValue(RBFNode.outWeights)
            
            outWeightBuilder = outWeightsListArrayDataHandle.builder()
            
                    
            if (srcCount != targCount) or (srcCount <= 1) or (inSwitchVal==False):
                return "unknown"
            else:
                srcKeys = np.zeros((srcCount,3), dtype=np.float64)
                targKeys = np.zeros((targCount,3), dtype=np.float64)
                
                for i in range(0, srcCount):
                    srcKeysListArrayDataHandle.jumpToElement(i)
                    srcKeyListDataHandle = srcKeysListArrayDataHandle.inputValue()
                    dataHandleSrcKey = srcKeyListDataHandle.child(RBFNode.inSrcKey)
                    inSrcKey = OpenMaya.MFloatVector()
                    inSrcKey = dataHandleSrcKey.asFloatVector()
                    for m in range(0,3):
                        srcKeys[i][m] = inSrcKey[m]
                        
                for i in range(0, targCount):
                    targKeysListArrayDataHandle.jumpToElement(i)
                    targKeyListDataHandle = targKeysListArrayDataHandle.inputValue()
                    dataHandleTargKey = targKeyListDataHandle.child(RBFNode.inTargKey)
                    inTargKey = OpenMaya.MFloatVector()
                    inTargKey = dataHandleTargKey.asFloatVector()
                    for m in range(0,3):
                        targKeys[i][m] = inTargKey[m]
                        
                origKeyPos = np.array(srcKeys, dtype=np.float64)
                targKeyPos = np.array(targKeys, dtype=np.float64)
                GCV = 1
                lambdaV = 10
                deltaAllowance =  0.000001
                
                minDistList = self.getMinDistList(origKeyPos)
                H = self.getInterpolateMatrixH(srcKeys, minDistList)
                eigens = self.getEigens(H)
                eigenValues = eigens[0]
                eigenVectors = eigens[1]
                Z = self.getTargProjToEigenZ(targKeys, eigenVectors)
                

                ignoreChangeCount = 0
                while (GCV>0.0001):
                    lambdaV = self.getLambdaV(eigenValues, lambdaV, Z)
                    newGCV = self.getGCV(lambdaV, Z, eigenValues)
                    deltaGCV = np.absolute(newGCV - GCV)
                    GCV = newGCV
                    if deltaGCV<0.00000001:
                        ignoreChangeCount += 1
                    if ignoreChangeCount>50:
                        break
                weight = self.calWeight(H, lambdaV, targKeys)
            
            if (outWeightBuilder.elementCount()==0):
                outWeightBuilder.addLast()
            else:
                amount = np.amin([srcCount, targCount])
                while (outWeightBuilder.elementCount()<amount) and (amount>0):
                    outWeightBuilder.addLast()
                while (outWeightBuilder.elementCount()>amount) and (amount>0):
                    outWeightBuilder.removeElement(outWeightBuilder.elementCount()-1)
            outWeightsListArrayDataHandle.set(outWeightBuilder)
            
            for i in range(0, outWeightBuilder.elementCount()):
                outWeightsListArrayDataHandle.jumpToElement(i)
                outWeightDataHandle = outWeightsListArrayDataHandle.outputValue()
                dataHandleWeight = outWeightDataHandle.child(RBFNode.outWeight)
                dataHandleWeight.set3Float(weight[i][0], weight[i][1], weight[i][2])
                
            outWeightsListArrayDataHandle.setAllClean()
            dataBlock.setClean(plug)

        else:
            return "unknown"


def nodeCreator():
    return OpenMayaMPx.asMPxPtr(RBFNode())


def nodeInitializer():
    mFnCompound = OpenMaya.MFnCompoundAttribute()
    mFnNumericAttr = OpenMaya.MFnNumericAttribute()
    
    #solve switch
    RBFNode.inSwitch = mFnNumericAttr.create("Solve", "solve", OpenMaya.MFnNumericData.kBoolean, 0) #set default value
    mFnNumericAttr.setReadable(1)
    mFnNumericAttr.setWritable(1)
    mFnNumericAttr.setStorable(1)
    mFnNumericAttr.setKeyable(1)
    RBFNode.addAttribute(RBFNode.inSwitch)
    
    #src keys
    RBFNode.inSrcKeys = mFnCompound.create("SrourceKeys", "srcKeysP")
    RBFNode.inSrcKey = mFnNumericAttr.create("srcKey", "srcKey", OpenMaya.MFnNumericData.k3Float)
    mFnNumericAttr.setKeyable(1)
    mFnNumericAttr.setReadable(1)
    mFnCompound.setArray(1)
    mFnCompound.addChild(RBFNode.inSrcKey)
    mFnCompound.setReadable(1)
    mFnCompound.setUsesArrayDataBuilder(1)
    RBFNode.addAttribute(RBFNode.inSrcKeys)
    
    #targ keys
    RBFNode.inTargKeys = mFnCompound.create("TargetKeys", "targKeysP")
    RBFNode.inTargKey = mFnNumericAttr.create("targKey", "targKey", OpenMaya.MFnNumericData.k3Float)
    mFnNumericAttr.setKeyable(1)
    mFnNumericAttr.setReadable(1)
    mFnCompound.setArray(1)
    mFnCompound.addChild(RBFNode.inTargKey)
    mFnCompound.setReadable(1)
    mFnCompound.setUsesArrayDataBuilder(1)
    RBFNode.addAttribute(RBFNode.inTargKeys)
    
    #weight
    RBFNode.outWeights = mFnCompound.create("Weights", "Weights")
    RBFNode.outWeight = mFnNumericAttr.create("weight", "weights", OpenMaya.MFnNumericData.k3Float)
    mFnNumericAttr.setWritable(0)
    mFnNumericAttr.setReadable(1)
    mFnCompound.setArray(1)
    mFnCompound.addChild(RBFNode.outWeight)
    mFnCompound.setReadable(1)
    mFnCompound.setUsesArrayDataBuilder(1)
    RBFNode.addAttribute(RBFNode.outWeights)
    
    RBFNode.attributeAffects(RBFNode.inSwitch, RBFNode.outWeights)
    RBFNode.attributeAffects(RBFNode.inSrcKeys, RBFNode.outWeights)
    RBFNode.attributeAffects(RBFNode.inTargKeys, RBFNode.outWeights)

   
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerNode(nodeName, nodeId, nodeCreator, nodeInitializer, OpenMayaMPx.MPxNode.kDependNode)
    except:
        sys.stderr.write("Faild to register node: " + nodeName + "; \n")


def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(nodeId)
    except:
        sys.stderr.write("Faild to deregister node: " + nodeName + "; \n")
        
