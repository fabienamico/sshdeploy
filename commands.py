# Deploying the application with SSH
# ~~~~

sys.path.append(os.path.join(module, 'python'))
import tarfile
import time
import sys
import ssh

escapeFiles = ['logs', 'eclipse', 'test-result', 'tmp', 'war', '.settings', '.project', '.classpath']

#
# Read the configuration file
#
def readConf(key):
	if application_path:
		keyRe = re.compile('^' + key + '\s*=')
		for line in open(os.path.join(application_path, 'conf/deployment-server.conf')).readlines():
			if keyRe.match(line):
				return line[line.find('=')+1:].strip()
	return ''

#
# Check if theString contains theQueryValue
#
def contains(theString, theQueryValue):
	return theString.find(theQueryValue) > -1

#
# Check if the file have to be escape
#
def isEscapeFile(fileName):
	for escapeFile in escapeFiles :
		if  contains(fileName, os.path.join(application_path, escapeFile)):
			return True
	return False

#
# Zip a directory
#
# zipdir("foo") : Just give it a dir and get a .zip file
# zipdir("foo", "foo2.zip") : Get a .zip file with a specific file name
# zipdir("foo", "foo3nodir.zip", False) : Omit the top level directory
# zipdir("../test1/foo", "foo4nopardirs.zip")
#
def zipdir(dirPath=None, zipFilePath=None, includeDirInZip=True):

	if not zipFilePath:
		zipFilePath = dirPath + ".zip"
	if not os.path.isdir(dirPath):
		raise OSError("dirPath argument must point to a directory. "
			"'%s' does not." % dirPath)
	parentDir, dirToZip = os.path.split(dirPath)
	#Little nested function to prepare the proper archive path
	def trimPath(path):
		archivePath = path.replace(parentDir, "", 1)
		if parentDir:
			archivePath = archivePath.replace(os.path.sep, "", 1)
		if not includeDirInZip:
			archivePath = archivePath.replace(dirToZip + os.path.sep, "", 1)
		return os.path.normcase(archivePath)

	outFile = zipfile.ZipFile(zipFilePath, "w",
		compression=zipfile.ZIP_DEFLATED)
	for (archiveDirPath, dirNames, fileNames) in os.walk(dirPath):
			for fileName in fileNames:
				## Suppress unused directory and file
				if not isEscapeFile(os.path.join(archiveDirPath, fileName)) :
					filePath = os.path.join(archiveDirPath, fileName)
					outFile.write(filePath, trimPath(filePath))

    #TODO : Make sure we get empty directories as well !!

	outFile.close()


#
# The deploy command
#
if play_command.startswith('sshdeploy:'):
	try:

		print '~'
		print '~ Create zip file  '  
		print '~ ---------'

		appName = os.path.basename(application_path) + '.zip' 

		if not os.path.exists(os.path.join(application_path, 'tmp', 'deploy')):
			os.mkdir(os.path.join(application_path, 'tmp', 'deploy'))
		
		tmpFile = os.path.join(application_path, 'tmp', 'deploy', appName)
		zipdir(application_path, tmpFile)

		print "~ File created : " + tmpFile

		deployEnv = play_command[play_command.find(':')+1:]

		userName=readConf(deployEnv+'.username')
		password= readConf(deployEnv+'.password')
		serverName= readConf(deployEnv+'.servername')
		path=readConf(deployEnv+'.path')

		print '~'
		print '~ Connect to the server : ' + serverName
		print '~ ---------'
		sshConnect = ssh.Connection(serverName, userName, password=password)
		
		print '~'
		print '~ Execute pre-deploy command'
		print '~ ---------'

		preCommand = readConf(deployEnv+'.precommand')
		commands = preCommand.split(';')
		for command in commands:
			print '~ Execute : ' + command
			sshConnect.execute(command)
		
		print '~'
		print '~ Copy file to the server : ' + deployEnv		
		print '~ Directory : ' + path
		print '~ ---------'
		sshConnect.put(tmpFile, path + '/' + appName)
		
		print "~ Unzip application " + path + '/' + appName 
		sshConnect.execute('unzip ' + path + '/' + appName + '-d /tmp' )
		
		print '~'
		print '~ Execute post deploy command'
		print '~ ---------'

		postCommand = readConf(deployEnv+'.postcommand')
		commands = postCommand.split(';')
		for command in commands:
			print '~ Execute : ' + command
			sshConnect.execute(command)
		
		sshConnect.close()

		print '~'
		print '~ Clean temp directory '		
		print '~ ---------'
		os.remove(tmpFile)

		sys.exit(0)
				
	except getopt.GetoptError, err:
		print "~ %s" % str(err)
		print "~ "
		sys.exit(-1)
		
	sys.exit(0)
