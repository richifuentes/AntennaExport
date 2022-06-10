import sys
from xml.dom import minidom
from suds.client import Client
import logging

if __name__ == '__main__':
    
    #save_path_file = "20072021_ANTENNA-LIST.RANX.xml"
        
    logging.basicConfig(filename='getLastVersionByAntennaName.log',level=logging.INFO,format='%(asctime)s %(message)s')
    logging.info('INFO: Script started')
    
    arguments = sys.argv  # get the list of arguments passed to the script.

    save_path_file = arguments[2] #  get file name from 3rd Argument from command.
    
    antenna_List = arguments[1].split(',') # get the 2 argument (antenna list to export) into a list

    all_Antennas_Suds = dict()  # This dict will hold all the antenna suds objects returned from the API

    user = 'ams2talend'
    pw = 'ams2talend'
    wsdl = 'http://demucvak35.viaginterkom.de:8090/antenna-manager-prod/ws/amsService?wsdl'
    #wsdl = 'http://demucvak35.viaginterkom.de:9090/antenna-manager-test/ws/amsService?wsdl'
    client = Client(url=wsdl, username=user, password=pw)  # Create SOAP Client.

    logging.info('INFO: ' + str(len(antenna_List)) + ' Antennas to be exported')

    #  This antenna list will hold all antennas that exists on AMS from the arguments
    #  It will be used for the Antenna Family Name as AntennaType is missing from AMS
    antennaNames = list()
    for i in range(len(antenna_List)):
        antenna = client.service.getLastVersionByAntennaName(antenna_List[i])
        if antenna == None:
            logging.warning('WARNING: ' + antenna_List[i] + ' was not found on AMS')
            all_Antennas_Suds[i] = antenna  # Add the Antenna suds object to the dictionary
            antennaNames.append(antenna_List[i])
            next
        else:
            all_Antennas_Suds[i] = antenna  # Add the Antenna suds object to the dictionary
            antennaNames.append(antenna_List[i])

    root = minidom.Document()   #  minidom constructor.

    # Set up of the RadioAccessNetwork tag for the RANX XML file.
    ran  = root.createElement("RadioAccessNetwork")
    ran.setAttribute("name", "null")
    ran.setAttribute("version", "3")
    ran.setAttribute("xmlns", "urn:schemas-actix-com:radio-access-network")
    root.appendChild(ran)

    # Put every antenna on a dict and later on the XML format
    for j in range(len(all_Antennas_Suds)):
        if all_Antennas_Suds[j] == None:
            next
        else:
            fullAntenna_dict = Client.dict(all_Antennas_Suds[j])
        
            # Commenting antennaType out to avoid AMS API Bug
            #antennaType = client.dict(fullAntenna_dict.get("antennaType"))  # Get the AntennyType attribute
            
            manufacturer = client.dict(fullAntenna_dict.get("manufacturer"))  # Get the manufacturer attribute
            owner = client.dict(fullAntenna_dict.get("operator"))  # Get the operator attribute
            antennaConfigs = client.items(fullAntenna_dict.get("configurations"))  # Get all antenna configurations (patterns)
            config_List = list(antennaConfigs)  # Put all patterns on a list

            #  Get every pattern to a dict
            config_Dict = dict()
            for x in range(len(config_List)):
                    a = client.dict(config_List[x])
                    config_Dict[x] = a

            angles = str() #  Create an string variable and fill it with the angles (0 to 360°).
            for y in range(0, 360, 1):
                    angles = angles + str(y) + " "

            #  Add the Antenna Type to the XML
            #  Commenting antennaType out to avoid AMS API Bug 
            #at = antennaType["name"]
            at = antennaNames[j]
            
            antennaType = root.createElement("AntennaType")
            antennaType.setAttribute("name", at)
            ran.appendChild(antennaType)
            #  logging antennas info for troubleshotting  #####
            #logging.info('INFO: Antenna Type: ' + at + ', manufacturer:' + manufacturer["name"])
                            
            for z in range(len(config_Dict)):
                    a = config_Dict[z]

                    #  Creating a lits of tags to avoid non ATOLL Patterns
                    tagsNames = list()
                    tagsList = list(a['tags'])
                    for o in range(len(tagsList)):
                            tagsdict = client.dict(tagsList[o])
                            tagsNames.append(tagsdict['name'])

                    if 'ATOLL' in tagsNames:
                            beamPattern = root.createElement("BeamPattern")
                            try:
                                    bP = a["exportName"]
                            except: bP = ""
                            beamPattern.setAttribute("name", bP)
                            
                            try:
                                    et = str(a["elTilt"])
                            except: et = ""
                            beamPattern.setAttribute("electricalDownTilt", et)
                            
                            try:
                                    fl = str(a["frequLow"])
                            except: fl = ""
                            beamPattern.setAttribute("frequencyRangeMin", fl)
                            
                            try:
                                    fh = str(a["frequHigh"])
                            except: fh = ""
                            beamPattern.setAttribute("frequencyRangeMax", fh)

                            antennaType.appendChild(beamPattern)

                            attribute1 = root.createElement("Attribute")
                            attribute1.setAttribute("name", "AntennaGroup")
                            attribute1.setAttribute("scope", "Common")
                            attribute1.setAttribute("type", "STRING")
                            try:
                                    manu = manufacturer["name"]
                            except: manu = ""
                            attribute1.setAttribute("value", manu)

                            beamPattern.appendChild(attribute1)

                            attribute2 = root.createElement("Attribute")
                            attribute2.setAttribute("name", "horizontalBeamwidth")
                            attribute2.setAttribute("scope", "Common")
                            attribute2.setAttribute("type", "FLOAT")
                            try:
                                    bw = str(a["beamWidthHor"])
                            except: bw = ""
                            attribute2.setAttribute("value", bw)

                            beamPattern.appendChild(attribute2)

                            attribute3 = root.createElement("Attribute")
                            attribute3.setAttribute("name", "isotropicGain")
                            attribute3.setAttribute("scope", "Common")
                            attribute3.setAttribute("type", "FLOAT")
                            try:
                                    isotropicGain = str(a["gain"])
                            except: isotropicGain = ""
                            attribute3.setAttribute("value", isotropicGain)

                            beamPattern.appendChild(attribute3)

                            attribute4 = root.createElement("Attribute")
                            attribute4.setAttribute("name", "horizontalPatternAngles")
                            attribute4.setAttribute("scope", "Common")
                            attribute4.setAttribute("type", "STRING")
                            attribute4.setAttribute("value", angles)

                            beamPattern.appendChild(attribute4)

                            attribute5 = root.createElement("Attribute")
                            attribute5.setAttribute("name", "horizontalPatternLosses")
                            attribute5.setAttribute("scope", "Common")
                            attribute5.setAttribute("type", "STRING")
                            horizontalPatternLosses = str()
                            try:
                                    hpl = a["diagramH"].split(";")
                            except: hpl = ""
                            for f in range(0,360):
                                    horizontalPatternLosses = horizontalPatternLosses + hpl[f] + " "
                            attribute5.setAttribute("value", horizontalPatternLosses)

                            beamPattern.appendChild(attribute5)

                            attribute6 = root.createElement("Attribute")
                            attribute6.setAttribute("name", "verticalPatternAngles")
                            attribute6.setAttribute("scope", "Common")
                            attribute6.setAttribute("type", "STRING")
                            attribute6.setAttribute("value", angles)

                            beamPattern.appendChild(attribute6)

                            attribute7 = root.createElement("Attribute")
                            attribute7.setAttribute("name", "verticalPatternLosses")
                            attribute7.setAttribute("scope", "Common")
                            attribute7.setAttribute("type", "STRING")
                            verticalPatternLosses = str()
                            try:
                                    vpl = a["diagramV"].split(";")
                            except: vpl = ""
                            for g in range(0,360):
                                    verticalPatternLosses = verticalPatternLosses + vpl[g] + " "
                            attribute7.setAttribute("value", verticalPatternLosses)

                            beamPattern.appendChild(attribute7)

                            #  Logging antennas info for troubleshotting ####
                            #logging.info('INFO: Antenna export Name: ' + bP + ', E-Tilt:' + et + ', frequlow: ' +
                                                     #fl + ', frequhigh: '+ fh + ', beamWidthHor: ' + bw + ', isotropicGain: ' +
                                                     #isotropicGain )
                            #logging.info('INFO: horizontalPatternLosses: ' + horizontalPatternLosses)
                            #logging.info('INFO: verticalPatternLosses: ' + verticalPatternLosses)

                    else:
                            continue    
            
    xml_str = root.toprettyxml(indent="\t", newl = '\n', encoding='UTF-8')

    logging.info('INFO: File ' + save_path_file + ' saved')

    with open(save_path_file, 'wb') as f: 
        f.write(xml_str)
                 
    logging.info('INFO: Script finished')
