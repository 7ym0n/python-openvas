#This aims at parsing the CLI args
import sys, signal, re, socket, argparse
from threading import Thread
from SocketConnect import *
from ParseOid import *
from ParseScan import *
from Email import *

def valid_ip(address):
    #check if an ip is valid or not
    try:
        b1 = socket.inet_pton(socket.AF_INET6,address)
        return True
    except:
        try:
            b2 = socket.inet_pton(socket.AF_INET,address)
            return True
        except:
           return False

argv=sys.argv[1:] #put the arguments in a string
parser = argparse.ArgumentParser(description="openvas-handler menu")
parser.add_argument('-a', '--all', help='Scan all the families', action='store_true')
parser.add_argument('-f', '--scan-families', metavar="family1,family2", dest='-i', type=str, nargs="+", help="Specify families for the families for the scan")
parser.add_argument('-i', '--ip', metavar='8.8.8.8', type=str ,dest='f', nargs=1, help="IP of the host to scan")
parser.add_argument('-j', '--json', help="Output the report in JSON",action='store_true')
parser.add_argument('-l', '--list-families', help="List the families available (ex: Windows, Linux, Cisco, etc)", action='store_true')
parser.add_argument('-s', '--email', metavar="x1@example.com,x2@example.com", type=str, nargs="+", help="Send the report to someone@example.com by email")
args = parser.parse_args()

if args.list_families:
    print("\033[32mWait for job to be completed, it can take a few seconds ...\033[0m")
    message= """< OTP/2.0 >
CLIENT <|> NVT_INFO <|> CLIENT
CLIENT <|> COMPLETE_LIST <|> CLIENT
"""
    outputVar = SocketConnect(message,3) #outputVar is the answer of scanner to message
    parserMatch = "SERVER <|> PLUGIN_LIST <|>\n"
    oid = ParseOid(parserMatch,outputVar) #Let's parse the answer of the scanner
    oid.SectionParser()
    #print the families available:
    print(oid.familyDict.keys())
    sys.exit(0)

elif opt in ("-i", "--ip"):
    regbool = valid_ip(arg)
    if regbool == True:
        #Prepare arguments for the attack
        ipScan = arg
    else:
        print("\033[1m\033[31mInvalid IP format !\033[0m \nYet, IPv6 and IPv4 handled.")
        sys.exit(1)

elif opt in ("-f","--scan-families"):
    familyScan = arg.split(",")

elif opt in ("-s","--email"):
    destinationList = arg.split(",")

#Do we have all the required args to run the scan
runScanBool = not ipScan and not familyScan
#Then run the scan:
if not runScanBool:
    print("\033[34mDon't forget to deactivate your firewall !\033[0m")
    print("\033[32mWait, we are retrieving the ID of the vulnerabilities to scan ...\033[0m")
    message= """< OTP/2.0 >
CLIENT <|> NVT_INFO <|> CLIENT
CLIENT <|> COMPLETE_LIST <|> CLIENT
"""
    outputVar = SocketConnect(message,3)
    parserMatch = "SERVER <|> PLUGIN_LIST <|>\n"
    oid = ParseOid(parserMatch,outputVar)
    oid.SectionParser()
    print("\033[32mPlease Wait, while we scan the device ...\033[0m")
    familyList = oid.familyDict.keys()
    oidList = []
    if args.all: #Let's scan all the families
        oidList = [family.keys() for family in oid.familyDict.values()]
        for i in familyList:
            oidList=oidList + oid.familyDict[i].keys() #output the oid in a list of the i family of familyList
    else:
        oidList = [family.keys() for (name, family) in oid.familyDict.items() if name in familyScan]
        for i in familyScan:
            oidList=oidList + oid.familyDict[i].keys() #output the oid in a list of the i family of familyList
    oidString = ';'.join(oidList)
    oidString[:-1] #Remove the first ","
    #Read the content of the configuration file --> confFile
    confFile = open("conf/scan.conf").read()
    message = """< OTP/2.0 >
CLIENT <|> PREFERENCES <|>
plugin_set <|> """ + oidString + "\n" + confFile + str(len(ipScan)) + "\n" +ipScan +"\n"
    outputScan = SocketConnect(message,300,True) #Launch the Socket interaction in verbose mode with a wait time of  300s to detect errors
    ####Parsing the Scan Section
    scanReport = ParseScan(outputScan,ipScan,oid.familyDict)
    ##### JSON Section
    if args.json: #Parse in Json
        scanReport.ParserJSON()
    #####Email Section
    if 'destinationList' in locals():
        scanReport.ParserEmail()
        s = Email(scanReport.report,destinationList)
        s.sendEmail()
        print("\033[32mEmail Sent!\033[0m")