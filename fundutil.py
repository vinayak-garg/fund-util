# Various utilities for analyizng Mutual fund portfolio
# Usage: python3 fundutil.py ~/path/to/transaction/data

import csv
import datetime
from enum import Enum
import os
import sys

class UserOption(Enum):
	INVESTMENT = 1

class TransactionType(Enum):
	BUY = 1
	SELL = 2
	OTHER = 3

class Transaction:
	def __init__(self):
		self.tDate = datetime.date.today()
		self.tType = TransactionType.OTHER
		self.tUnits = 0
		self.tPrice = 0
		self.tAmount = 0

class Holding:
	def __init__(self):
		self.hDate = datetime.date.today()
		self.hUnits = 0
		self.hRemainingUnits = 0
		self.hPrice = 0

	def __init__(self, transaction):
		self.hDate = transaction.tDate
		self.hUnits = transaction.tUnits
		self.hRemainingUnits = transaction.tUnits
		self.hPrice = transaction.tPrice

class Scheme:
	def __init__(self):
		self.sCode = ''
		self.sName = ''
		self.sTransactions = []
		self.sHoldings = []

class Folio:
	def __init__(self):
		self.fNum = ''
		self.fAMCName = ''
		self.fSchemes = []

#
def Err(inErrStr):
	print(inErrStr)
	exit()

#
def Currency(inNum):
	return '₹{:0,.2f}'.format(inNum).replace('₹-', '-₹')

#
def GetWorkingPath():
	workingPath = os.getcwd()
	if len(sys.argv) >= 2:
		workingPath = sys.argv[1]

	return workingPath

#
def GetCSVFilePaths():
	workingPath = GetWorkingPath()

	paths = []
	for f in os.listdir(workingPath):
		if f.endswith('.csv'):
			paths.append(os.path.join(workingPath, f))

	return paths

#
def GetSchemeCodeFromCAMSCode(inCamsCode, inFundName):
	camsCodeToSchemeCode = [
		['L103G', '103504'],	# SBI Blue Chip Fund Reg Plan-G
		['LD040A', '119707'],	# SBI Magnum Gilt Fund Direct Growth
		['LD069G', '119824'],	# SBI Magnum Medium Duration F Dir Gr
		['LD091G', '119716'],	# SBI Magnum MidCap Dir Fund-G
		['LD099G', '119718'],	# SBI Flexicap Fund-Dir Gr
		['LD103G', '119598'],	# SBI Blue Chip Fund Dir Plan-G
		['P11', '100349'],		# ICICI Large & Mid Cap Fund - Growth
		['P8034', '120591'],	# ICICI Smallcap Fund - Direct Plan Growth
		['P8101', '120211'],	# ICICI Money Market Fund -Drt Growth
		['P8133', '120186'],	# ICICI US Bluechip Equity Fund -Drt Growth
		['P8145', '120603'],	# ICICI All Seasons Bond Fund - DP Growth
		['P8189', '120620'],	# ICICI Nifty 50 Index Fund-DP Growth
		['P9656', '149219'],	# ICICI NASDAQ 100 Index Fund - DP-Growth
		['FTI035', '100526'],	# FTI ELSS TAX SAVER - IDCW
		['FTI484', '118559'],	# FTI Asian Equity Fund - DP - Growth
		['B153GZ', '119568'],	# ABSL Liquid Fund - Growth-DIRECT
		['B291GZ', '119591'],	# ABSL India GenNext Fund - Growth-DIRECT
		['B295GZ', '119556'],	# ABSL Small Cap Fund Growth-DIRECT
	]

	for entry in camsCodeToSchemeCode:
		if entry[0] == inCamsCode:
			return entry[1]

	Err('Error: Could not find mapping from CAMS code to MF Scheme code for ' + inFundName)

#
def GetFolioIndex(inFolioNum, ioFolios):
	for i, entry in enumerate(ioFolios):
		if entry.fNum == inFolioNum:
			return i
	newFolio = Folio()
	newFolio.fNum = inFolioNum
	ioFolios.append(newFolio)
	return len(ioFolios) - 1

#
def GetSchemeIndex(inSchemeCode, ioFolio):
	for i, entry in enumerate(ioFolio.fSchemes):
		if entry.sCode == inSchemeCode:
			return i
	newScheme = Scheme()
	newScheme.sCode = inSchemeCode
	ioFolio.fSchemes.append(newScheme)
	return len(ioFolio.fSchemes) - 1

#
def ParseDate(inDateStr, src):
	try:
		dateObject = datetime.datetime.strptime(inDateStr, '%d-%b-%Y').date()
	except Exception:
		Err('Error: Unable to parse date from ' + src + ' \'' + inTransactionDateStr + '\'. Required format dd-mmm-yyyy')
	return dateObject

#
def ParseTransactionType(inTransactionTypeStr):
	lowerCaseTransactionType = inTransactionTypeStr.lower()
	if (lowerCaseTransactionType.find('purchase') >= 0 or
		lowerCaseTransactionType.find('switch in') >= 0):
		return TransactionType.BUY
	if (lowerCaseTransactionType.find('redemption') >= 0 or
		lowerCaseTransactionType.find('switch out') >= 0):
		return TransactionType.SELL
	return TransactionType.OTHER

#
def PrepareTransaction(inCsvEntry):
	transactionDate = inCsvEntry[7]
	transactionType = inCsvEntry[8]
	amount = inCsvEntry[10]
	units = inCsvEntry[11]
	price = inCsvEntry[12]

	transaction = Transaction()
	transaction.tDate = ParseDate(transactionDate, 'csv')
	transaction.tType = ParseTransactionType(transactionType)
	if transaction.tType != TransactionType.OTHER:
		transaction.tUnits = float(units)
		transaction.tPrice = float(price)
		transaction.tAmount = float(amount)

	return transaction


#
def ParseCSVEntry(inCsvEntry, ioFolios):
	mfName = inCsvEntry[0]
	folioNum = inCsvEntry[3]
	camsCode = inCsvEntry[4]
	schemeName = inCsvEntry[5]
	schemeType = inCsvEntry[6]

	if folioNum == '':
		return

	schemeCode = GetSchemeCodeFromCAMSCode(camsCode, schemeName)

	folioIndex = GetFolioIndex(folioNum, ioFolios)
	folio = ioFolios[folioIndex]
	folio.fAMCName = mfName

	schemeIndex = GetSchemeIndex(schemeCode, folio)
	scheme = folio.fSchemes[schemeIndex]
	scheme.sName = schemeName
	scheme.sTransactions.append(PrepareTransaction(inCsvEntry))

#
def ParseCSVFile(inCsvPath, ioFolios):
	# 'utf-8-sig' tells python to interpret BOM mark at the start of file data
	# so that it is not included as part of actual read data
	with open(inCsvPath, encoding='utf-8-sig') as csvFile:
		csvData = csv.reader(csvFile)
		for i, row in enumerate(csvData):
			if i == 0:
				# Skip the header in csv
				continue
			ParseCSVEntry(row, ioFolios)

# Probably unnecessary, but better to do it to ensure the holdings are correct
def SortTransactions(inFolios):
	for folio in inFolios:
		for scheme in folio.fSchemes:
			scheme.sTransactions.sort(key=lambda transaction: transaction.tDate)

#
def PrepareHoldings(inFolios):
	for folio in inFolios:
		for scheme in folio.fSchemes:
			for transaction in scheme.sTransactions:
				if transaction.tType == TransactionType.BUY:
					scheme.sHoldings.append(Holding(transaction))
				elif transaction.tType == TransactionType.SELL:
					soldUnits = -transaction.tUnits
					for holding in scheme.sHoldings:
						if holding.hRemainingUnits > soldUnits:
							holding.hRemainingUnits -= soldUnits
							soldUnits = 0
							break
						else:
							soldUnits -= holding.hRemainingUnits
							holding.hRemainingUnits = 0
							if soldUnits <= 0:
								break
					if soldUnits > 1e-9:
						Err('Error: Sold more units then we were holding!!')


#
def PrepareMutualFundData():
	folios = []

	csvPaths = GetCSVFilePaths()

	if len(csvPaths) == 0:
		Err('Error: did not find any .csv file in working directory')

	for csvPath in csvPaths:
		ParseCSVFile(csvPath, folios)

	SortTransactions(folios)
	PrepareHoldings(folios)

	return folios

#
def PrintInvestmentInRange(inFolios, startDate, endDate):
	
	print('Fund wise summary of invested amount - ')
	print('-'*100)

	fundInvestmentMap = {}
	for folio in inFolios:
		if folio.fAMCName not in fundInvestmentMap:
			fundInvestmentMap[folio.fAMCName] = 0
		entryCount = 0
		for scheme in folio.fSchemes:
			schemeTotal = 0
			for transaction in scheme.sTransactions:
				if (transaction.tType == TransactionType.BUY and
					transaction.tDate >= startDate and
					transaction.tDate <= endDate):
					schemeTotal += transaction.tAmount
			
			fundInvestmentMap[folio.fAMCName] += schemeTotal
			if schemeTotal > 0:
				print(scheme.sName + '\t' + Currency(schemeTotal))
				entryCount += 1

		if entryCount > 0:
			print('-'*100)

	print()
	print('AMC wise aggregated summary of invested amount - ')
	print('-'*100)
	total = 0
	for key in fundInvestmentMap:
		val = fundInvestmentMap[key]
		print(key, Currency(val))
		total += val

	print('-'*100)
	print('Total cost of investment ' + Currency(total))
	print('-'*100)

#
def ParseStartAndEndDate(inDateRangeStr):
	dates = inDateRangeStr.split(':')
	if len(dates) != 2:
		Err('Error: Incorrect range provided \''+inDateRangeStr+'\'. Sample format \'01-dec-2023:31-dec-2023\'')

	if dates[0] == '':
		startDate = datetime.date(2000, 1, 1)
	else:
		startDate = ParseDate(dates[0], 'command args')

	if dates[1] == '':
		endDate = datetime.date.today()
	else:
		endDate = ParseDate(dates[1], 'command args')

	if startDate > endDate:
		Err('Error: start date \'' + dates[0] + '\' should be earlier than end date \'' + dates[1] + '\'')

	return (startDate, endDate)

#
def HandleUserInput(inFolios):
	givenOption = UserOption.INVESTMENT
	givenRangeStr = ':'

	if len(sys.argv) >= 3:
		userInput = sys.argv[2]
		if userInput.startswith('-i='):
			givenOption = UserOption.INVESTMENT
			givenRangeStr = userInput[3:]

	if givenOption == UserOption.INVESTMENT:
		startDate, endDate = ParseStartAndEndDate(givenRangeStr)
		PrintInvestmentInRange(inFolios, startDate, endDate)

#
def main():
	folios = PrepareMutualFundData()

	HandleUserInput(folios)


if __name__ == "__main__":
	main()
