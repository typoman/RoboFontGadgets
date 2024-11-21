from fontTools import designspaceLib
import fontgadgets.extensions.font
from fontgadgets import FontGadgetsError, getEnvironment
try:
    from ufoProcessor import ufoOperator
except ImportError:
    if getEnvironment() == "RoboFont":
        raise FontGadgetsError("You need to install `Designspace Editor 2` extension.")
    raise FontGadgetsError("ِInstall the latest version of ufoProcessor from:"
                           "https://github.com/LettError/ufoProcessor.git")
from mutatorMath.objects.location import Location
import os

def getSwapMapFromRulesAndLoationForGlyphNames(rules, location, glyphNames):
    """
    process design space rules into a dict of glyphName1 -> glyphName2
    """
    swapMap = {}
    glyphNames = set(glyphNames)
    for rule in rules:
        if designspaceLib.evaluateRule(rule, location):
            for glyphName1, glyphName2 in rule.subs:
                if glyphName1 in glyphNames:
                    swapMap[glyphName1] = glyphName2
    return swapMap

# subclass of ufoProcessor.ufoOperator.UFOOperator to process the swapping of
# the glyphs in designspace rules when generating the instances

class InterpolateFontsFromDesignSpace(ufoOperator.UFOOperator):

    """
    usage:
    generateInstances = InterpolateFontsFromDesignSpace(ds5Path)
    generateInstances.generateInstancesWithRules(useVarlib=False)
    """

    def generateInstancesWithRules(self, useVarlib=None, roundGeometry=True):
        """
        Interpolates and returns a dictionary of {'instance.path': genereatedFont}
        with designspace rules applied to the glyphs.
        This method will save the generated fonts.
        """
        self.roundGeometry = roundGeometry
        previousModel = self.useVarlib
        generatedFonts = {}
        if useVarlib is not None:
            self.useVarlib = useVarlib
        glyphCount = 0
        self.loadFonts()
        for instanceDescriptor in self.doc.instances:
            if instanceDescriptor.path is None:
                continue
            font = self.makeInstanceWithRules(instanceDescriptor, glyphNames=self.glyphNames,
                                              decomposeComponents=False)
            instanceFolder = os.path.dirname(instanceDescriptor.path)
            if not os.path.exists(instanceFolder):
                os.makedirs(instanceFolder)
            font.save(instanceDescriptor.path)
            generatedFonts[instanceDescriptor.path] = font
            glyphCount += len(font)
        self.useVarlib = previousModel
        return generatedFonts

    def makeInstanceWithRules(self, instanceDescriptor, glyphNames=None, decomposeComponents=False):
        # this method will apply the swapping rules to glyphs
        font = self.makeInstance(instanceDescriptor, glyphNames=glyphNames,
                                 decomposeComponents=decomposeComponents)
        fullDesignLocation = instanceDescriptor.getFullDesignLocation(self.doc)
        continuousLocation, discreteLocation = self.splitLocation(fullDesignLocation)
        if not self.extrapolate:
            continuousLocation = self.clipDesignLocation(continuousLocation)
        loc = Location(continuousLocation)
        swapNamesMap = getSwapMapFromRulesAndLoationForGlyphNames(self.rules, loc, self.glyphNames)
        font.swapGlyphNames(swapNamesMap, component_references=True, kerning_references=True,
                   groups_references=True, glyphorder_references=False) # same as ufoprocessor and ufo2ft ver 2.7.1.dev722+g71ef6ca.d20221024
        return font

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Generate ufo instances from a designspace file with the swap rules applied to the glyphs.')
    parser.add_argument('designspacepath', help='Path to the design space file')
    parser.add_argument('--use-varlib', action='store_true', help='Whether to use varlib')
    args = parser.parse_args()

    generateInstances = InterpolateFontsFromDesignSpace(args.designspacepath)
    generateInstances.generateInstancesWithRules(useVarlib=args.use_varlib)
