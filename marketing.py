"""
<textarea id="wpTextbox1" name="wpTextbox1" cols="80" rows="25" readonly="">
==Articles==
===Collated===
*[[Home Remedy]] - Source: [http://en.wikibooks.org/wiki/Ethnomedicine/Ethnomedicine_by_Illness Ethnomedicine by Illness] and [http://en.wikibooks.org/wiki/Ethnomedicine/Home_Remedies Home Remedies] - Improvement: Combined wikibooks with wikipedia articles

===Original===
*[[:Arthritis]] - Source: Original
*[[:Devcoin]] - Source: [https://github.com/Unthinkingbit/charity/blob/master/devcoin.html https://github.com/Unthinkingbit/charity/blob/master/devcoin.html]

==Link==
https://raw.github.com/Unthinkingbit/charity/master/devcoin.html

==Tip==
Coin Address: 17vec4jQGCzMEsTnivizHPaowE715tu2CB
</textarea>


Account is a program to generate a devcoin receiver file from a bitcoinshare, bounty, devcoinshare and peer file.

This is meant to be used by devcoin accountants and auditors to create and check the receiver files.  The account file has a list of addresses and shares.  Anything after a dash is a comment.


==Commands==
===Help===
The -h option, the -help option, will print the help, which is this document.  The example follows:
python account.py -h

===Input===
Default is https://raw.github.com/Unthinkingbit/charity/master/account_3.csv

The -input option sets the input file name.  The example follows:
python account.py -input https://raw.github.com/Unthinkingbit/charity/master/account_3.csv

An example of an account information input file is at:
https://raw.github.com/Unthinkingbit/charity/master/account_3.csv

===Output===
Default is test_receiver.csv

The -output option sets the output.  If the output ends with stderr, the output will be sent to stderr  If the output ends with stdout, the output will be sent to stdout.  If the output does not end with stderr or stdout, the output will be written to a file by that name, with whatever suffix the input file has.  The example follows:
python genereceiver.py -output test_receiver.csv

An example of an genereceiver output file is at:
https://raw.github.com/Unthinkingbit/charity/master/test_receiver_3.csv


==Install==
For genereceiver to run, you need Python 2.x, almoner will probably not run with python 3.x.  To check if it is on your machine, in a terminal type:
python

If python 2.x is not on your machine, download the latest python 2.x, which is available from:
http://www.python.org/download/
"""

import account
import almoner
import cStringIO
import sys
import tomecount


__license__ = 'MIT'


def getMarketingEarningsText(publishers):
	'Get the marketing earnings text.'
	cString = cStringIO.StringIO()
	for publisher in publishers:
		if publisher.payoutFifth != 0:
			publisher.write(cString)
	return cString.getvalue()

def getPublishers(lines, workerAddressSet):
	'Get the publishers.'
	publishers = []
	for line in lines:
		publisher = Publisher(line)
		if len(publisher.coinAddressSet.intersection(workerAddressSet)) > 0:
			publishers.append(publisher)
		else:
			print('%s did not work this round.' % publisher.name)
	return publishers

def getWorkerAddressSet(outputEarningsTo):
	'Get the worker addresses.'
	suffixNumber = 22
	fileName = 'bounty_%s.csv' % suffixNumber
	accountLines = account.getAccountLines([], fileName)
	receiverLines = account.getReceiverLines(accountLines, suffixNumber)
	workerAddresses = []
	for receiverLine in receiverLines:
		splitLine = receiverLine.split(',')
		workerAddresses += splitLine
	return set(workerAddresses)

def writeOutput(arguments):
	'Write output.'
	if '-h' in arguments or '-help' in arguments:
		print(__doc__)
		return
	fileName = almoner.getParameter(arguments, 'publishers.csv', 'input')
	lines = almoner.getTextLines(almoner.getFileText(fileName))
	outputEarningsTo = almoner.getParameter(arguments, 'marketing_earnings_???.csv', 'outputearnings')
	workerAddressSet = getWorkerAddressSet(outputEarningsTo)
	publishers = getPublishers(lines, workerAddressSet)
	marketingEarningsText = getMarketingEarningsText(publishers)
	if almoner.sendOutputTo(outputEarningsTo, marketingEarningsText):
		print('The marketing earnings bounty file has been written to:\n%s\n' % outputEarningsTo)


class Publisher:
	'A class to handle a publisher.'
	def __init__(self, line):
		'Initialize.'
		splitLine = line.split(',')
		self.coinAddress = splitLine[1]
		self.coinAddressSet = set(splitLine[1 :])
		self.domainPayout = 0
		self.name = splitLine[0]
		self.payoutFifth = 0
		self.postPayout = 0
		self.postWords = 0
		self.signaturePayout = False
		self.sourceAddress = 'http://devtome.com/doku.php?id=wiki:user:%s&do=edit' % self.name
		self.subdomainPayout = 0
		print('\nLoading pages from %s' % self.name)
		sourceText = tomecount.getSourceText(self.sourceAddress)
		isLink = False
		isPost = False
		isSignature = False
		for line in almoner.getTextLines(sourceText):
			lineStrippedLower = line.strip().lower()
			if '==' in lineStrippedLower:
				isLink = False
				isPost = False
				isSignature = False
				if 'link' in lineStrippedLower:
					isLink = True
				if 'post' in lineStrippedLower:
					isPost = True
				if 'signature' in lineStrippedLower:
					isSignature = True
			if isLink:
				self.addLinkPayout(lineStrippedLower)
			if isPost:
				self.addPostPayout(lineStrippedLower)
			if isSignature:
				self.addSignaturePayout(lineStrippedLower)
		if self.domainPayout == 0:
			if self.subdomainPayout == 1:
				self.payoutFifth += 1
				print('Subdomain payout: 1')
		if self.postWords > 100:
			if self.postWords > 1000:
				self.payoutFifth += 2
				print('Big post payout: 2')
			else:
				self.payoutFifth += 1
				print('Small post payout: 1')
		if self.payoutFifth > 0:
			print('Total payout fifths: %s' % self.payoutFifth)

	def addLinkPayout(self, lineStrippedLower):
		'Add link payout if there is a devtome link.'
		if lineStrippedLower.startswith('*'):
			lineStrippedLower = lineStrippedLower[1 :]
		if not lineStrippedLower.startswith('http'):
			return
		if self.domainPayout > 4:
			return
		originalLink = lineStrippedLower
		if lineStrippedLower.startswith('http://'):
			lineStrippedLower = lineStrippedLower[len('http://') :]
		elif lineStrippedLower.startswith('https://'):
			lineStrippedLower = lineStrippedLower[len('https://') :]
		if lineStrippedLower.startswith('www.'):
			lineStrippedLower = lineStrippedLower[len('www.') :]
		if lineStrippedLower.startswith('vps.'):
			lineStrippedLower = lineStrippedLower[len('vps.') :]
		if lineStrippedLower.endswith('/'):
			lineStrippedLower = lineStrippedLower[: -1]
		if '/' in lineStrippedLower:
			if self.subdomainPayout == 0:
				linkText = almoner.getInternetText(originalLink)
				if 'devtome.com' not in linkText:
					return
				self.subdomainPayout = 1
			return
		linkText = almoner.getInternetText(originalLink)
		if 'devtome.com' not in linkText:
			return
		self.domainPayout += 1
		self.payoutFifth += 2
		printString = 'Domain name payout: 2, Address: %s' % lineStrippedLower
		beginIndex = linkText.find('devtome.com')
		while beginIndex != -1:
			endIndex = linkText.find('</a>', beginIndex)
			if endIndex == -1:
				print(printString)
				return
			linkString = linkText[beginIndex : endIndex]
			if '<img' in linkString:
#			if '<img' in linkString and '728' in linkString and '90' in linkString:
				self.payoutFifth += 1
				print('Banner payout: 3, Address: %s' % lineStrippedLower)
				return
			beginIndex = linkText.find('devtome.com', endIndex)
		print(printString)

	def addPostPayout(self, lineStrippedLower):
		'Add post payout if there is a devtome link.'
		if lineStrippedLower.startswith('*'):
			lineStrippedLower = lineStrippedLower[1 :]
		if not lineStrippedLower.startswith('http'):
			return
		if self.postPayout > 4:
			return
		linkText = almoner.getInternetText(lineStrippedLower)
		if '#' in lineStrippedLower:
			lineStrippedLower = lineStrippedLower[: lineStrippedLower.find('#')]
		if ';' in lineStrippedLower:
			lineStrippedLower = lineStrippedLower[: lineStrippedLower.find(';')]
		messageString = '<a class="message_number" style="vertical-align: middle;" href="' + lineStrippedLower
		if messageString not in linkText:
			return
		postBeginIndex = linkText.find(messageString)
		postBeginIndex = linkText.find('<div class="post"', postBeginIndex)
		if postBeginIndex == -1:
			return
		postEndIndex = linkText.find('<td valign="bottom"', postBeginIndex + 1)
		linkText = linkText[postBeginIndex : postEndIndex]
		if 'devtome.com' not in linkText:
			return
		self.postWords += len(linkText.split())
		self.postPayout += 1

	def addSignaturePayout(self, lineStrippedLower):
		'Add signature payout if there is a devtome link.'
		if lineStrippedLower.startswith('*'):
			lineStrippedLower = lineStrippedLower[1 :]
		if not lineStrippedLower.startswith('http'):
			return
		linkText = almoner.getInternetText(lineStrippedLower)
		if 'devtome.com' not in linkText:
			return
		if self.signaturePayout:
			return
		self.signaturePayout = True
		postString = '<td><b>Posts: </b></td>'
		postIndex = linkText.find(postString)
		if postIndex == -1:
			return
		postEndIndex = postIndex + len(postString)
		postNumberEndIndex = linkText.find('</td>', postEndIndex + 1)
		if postNumberEndIndex == -1:
			return
		postNumberString = linkText[postEndIndex : postNumberEndIndex].strip()
		if '>' in postNumberString:
			postNumberString = postNumberString[postNumberString.find('>') + 1 :]
		postNumber = int(postNumberString)
		if postNumber > 1000:
			self.payoutFifth += 2
			print('Big signature payout: 2')
		else:
			self.payoutFifth += 1
			print('Small signature payout: 1')

	def write(self, cString):
		'Initialize.'
		cString.write('%s,%s,%s/5-Marketing(%s)\n' % (self.name, self.coinAddress, self.payoutFifth, self.sourceAddress))


def main():
	'Write output.'
	writeOutput(sys.argv)

if __name__ == '__main__':
	main()
