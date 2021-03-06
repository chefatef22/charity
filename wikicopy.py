"""
Wikicopy is a program to download the articles of a dokuwiki and save them in a zip file.


==Commands==
===Help===
The -h option, the -help option, will print the help, which is this document. The example follows:
python account.py -h

===Input===
Default is http://devtome.com

The -input option sets the input file name. The example follows:
python wikicopy.py -input http://devtome.com


==Install==
For wikicopy to run, you need Python 2.x, wikicopy will probably not run with python 3.x. To check if it is on your machine, in a terminal type:
python

If python 2.x is not on your machine, download the latest python 2.x, which is available from:
http://www.python.org/download/
"""

import almoner
import datetime
import os
import shutil
import sys
import tarfile
import time
import zipfile


__license__ = 'MIT'


globalDateTimeFormat = '%y/%m/%d %H:%M'


def getRecentTitles(archiveType, fileNameRoot, wikiAddress):
	'Get all titles of the dokuwiki.'
	archiveFileName = fileNameRoot + '.' + archiveType
	if not os.path.exists(archiveFileName):
		return getTitles(wikiAddress)
	if archiveType == 'zip':
		zipArchive = zipfile.ZipFile(archiveFileName, 'r')
		zipArchive.extractall(fileNameRoot)
		zipArchive.close()
	else:
		mode = 'r'
		if archiveType == 'bz2':
			mode = 'r:bz2'
		tarArchive = tarfile.open(archiveFileName, mode)
		tarArchive.extractall(fileNameRoot)
		tarArchive.close()
	lastModifiedText = almoner.getFileText(os.path.join(fileNameRoot, 'last_modified.txt'))
	lastModifiedDatetime = datetime.datetime.strptime(lastModifiedText, globalDateTimeFormat)
	print('Last modified: %s' % lastModifiedDatetime)
	nowDatetime = datetime.datetime.today()
	nowMinusLast = nowDatetime - lastModifiedDatetime
	print('Now minus last: %s' % nowMinusLast)
	twentySixHours = 26 * 3600
	if getSeconds(nowMinusLast) > (24 * 5 + 22) * 3600:
		return getTitles(wikiAddress)
	recentPageAddress = wikiAddress + '/doku.php?do=recent&id=start&show_changes=pages&first[0]'
	lines = almoner.getTextLines(almoner.getInternetText(recentPageAddress))
	lineDatetime = None
	dateTitle = 'class="date">'
	linkTitle = 'class="wikilink1" title="'
	nameTitle = 'name="'
	start = 0
	titleSet = set([])
	while True:
		for lineIndex, line in enumerate(lines):
			if dateTitle in line:
				dateLine = lines[lineIndex + 1]
				dateString = dateLine[: dateLine.find('<')]
				if dateString.startswith('20'):
					dateString = dateString[2 :]
				lineDatetime = datetime.datetime.strptime(dateString, globalDateTimeFormat)
			if linkTitle in line:
				line = line[line.find(linkTitle) + len(linkTitle) :]
				title = line[: line.find('"')]
				if title != 'start':
					lastMinusLine = lastModifiedDatetime - lineDatetime
					if title in titleSet or getSeconds(lastMinusLine) > twentySixHours:
						titles = list(titleSet)
						titles.sort()
						return titles
					titleSet.add(title)
			if line.startswith('<input') and 'value="less recent' in line and nameTitle in line:
				line = line[line.find(nameTitle) + len(nameTitle) :]
				name = line[: line.find('"')]
				recentPageAddress = wikiAddress + '/doku.php?do=recent&id=start&show_changes=pages&' + name
		lines = almoner.getTextLines(almoner.getInternetText(recentPageAddress))
	return getTitles(wikiAddress)

def getSeconds(timedelta):
	'Get the total number of seconds.'
	return timedelta.days * 86400 + timedelta.seconds

def getTitles(wikiAddress):
	'Get all titles of the dokuwiki.'
	indexDepth = 0
	popularPageAddress = wikiAddress + '/doku.php?id=start&idx=wiki%3Auser'
	lines = almoner.getTextLines(almoner.getInternetText(popularPageAddress))
	prefix = '?id='
	prefixLength = len(prefix)
	titles = []
	for line in lines:
		if line.startswith('</ul>'):
			if indexDepth > 0:
				indexDepth -= 1
		if indexDepth > 0 and 'class="wikilink1"' in line:
			prefixIndex = line.find(prefix) + prefixLength
			title = line[prefixIndex :]
			quoteIndex = title.find('"')
			if len(title) > 0:
				titles.append(title[: quoteIndex])
		if line == '<ul class="idx">':
			indexDepth += 1
	return titles

def writeOutput(arguments):
	'Write output.'
	if '-h' in arguments or '-help' in arguments:
		print(__doc__)
		return
	wikiAddress = almoner.getParameter(arguments, 'http://devtome.com', 'wiki')
	fileNameRoot = wikiAddress
	if 'http://' in fileNameRoot:
		fileNameRoot = fileNameRoot[len('http://') :]
	if '.' in fileNameRoot:
		fileNameRoot = fileNameRoot[: fileNameRoot.find('.')]
	archiveType = 'zip'
	archiveString = almoner.getParameter(arguments, 'zip', 'archive').lower()
	if archiveString.startswith('t'):
		archiveType = 'tar'
	elif archiveString.startswith('b'):
		archiveType = 'bz2'
	fileNameRoot = almoner.getParameter(arguments, fileNameRoot, 'output')
	shouldMakeSnapshot = almoner.getBoolean(arguments, 'false', 'snapshot')
	writeZipFile(archiveType, fileNameRoot, shouldMakeSnapshot, wikiAddress)

def writeTarFileByFolder(archiveType, archiveFileName, backupFolder):
	'Write tar file from a folder and remove that folder.'
	if archiveFileName in os.listdir(os.getcwd()):
		os.remove(archiveFileName)
	mode = 'w'
	if archiveType == 'bz2':
		mode = 'w:bz2'
	tarArchive = tarfile.open(archiveFileName, mode)
	backupFileNames = os.listdir(backupFolder)
	for backupFileName in backupFileNames:
		tarArchive.add(os.path.join(backupFolder, backupFileName), backupFileName)
	tarArchive.close()
	print('The tar file has been written to:\n%s\n' % archiveFileName)
	if os.path.isdir(backupFolder):
		shutil.rmtree(backupFolder)

def writeZipFile(archiveType, fileNameRoot, shouldMakeSnapshot, wikiAddress):
	'Write zip file.'
	print('Copying:')
	print(wikiAddress)
	print('')
	almoner.makeDirectory(fileNameRoot)
	previousLetter = '0'
	lastModifiedText = datetime.datetime.today().strftime(globalDateTimeFormat)
	titles = getRecentTitles(archiveType, fileNameRoot, wikiAddress)
	print('Number of titles: %s' % len(titles))
	almoner.writeFileText(os.path.join(fileNameRoot, 'last_modified.txt'), lastModifiedText)
	for title in titles:
		letter = title[0]
		if letter != previousLetter:
			previousLetter = letter
			print('Copying articles starting with %s.' % letter.upper())
		sourceText = almoner.getSourceText(wikiAddress + '/doku.php?id=%s&do=edit' % title)
		time.sleep(2)
		fileName = os.path.join(fileNameRoot, title)
		almoner.writeFileText(fileName, sourceText)
	print('There were %s files in the wiki.\n' % len(titles))
	archiveFileName = fileNameRoot + '.' + archiveType
	if archiveType == 'zip':
		almoner.writeZipFileByFolder(fileNameRoot)
	else:
		writeTarFileByFolder(archiveType, archiveFileName, fileNameRoot)
	if shouldMakeSnapshot:
		snapshotSuffix = datetime.datetime.today().strftime('_%y-%m-%d_%H')
		destination = fileNameRoot + snapshotSuffix + '.' + archiveType
		shutil.copyfile(archiveFileName, destination)
		print('The snapshot zip file has been written to:\n%s\n' % destination)


def main():
	'Write output.'
	writeOutput(sys.argv)

if __name__ == '__main__':
	main()
