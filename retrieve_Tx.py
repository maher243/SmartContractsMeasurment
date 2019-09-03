"""
Created on Wed Apr 10 17:21:42 2019

@author: b6068199
"""
from etherscanAPI import etherscan
import pandas as pd
import time
import xlrd

apikey = 'VGXFYKNBJ7K43G263YUET45CG522BT18KB' #use your own api key
myapi = etherscan(apikey, 'mainnet')

def get_contractCreation_code(to):
    try:
        '''
        get the first transaction sent to the contract account (usually the first one is the one that created the contract)
        '''
        tx= myapi.getTransactions(to,0,9999999999,1,1)
        creation_code= tx[0]['input'] # get the byte code of the creation transaction
        TO = tx[0]['to']
        if (TO != ''):
            creation_code= "error"

    except Exception:
        creation_code = "error"

    return creation_code


#currentblock = int(myapi.getBlockNumber(),16)  # to retrieve from last block
currentblock = 7453500 # start downloading transactons from this block
txlist = []
i = 0
txcount = 0
totaltx = 1000 # total number of transactions to be downloaded

while txcount < totaltx:
    try:
        block = myapi.getBlockByNumber(currentblock-i)
        txlist.append(block['transactions'])
        txcount = txcount + len(block['transactions'])
    except Exception as exception:
        time.sleep (1)  # Seconds

'''
txlist: a list of all the retrieved transactions.
It contains block hash, block number, tx sender, gas limit, gas price, tx hash, tx input, tx nonce, tx singature, receipint address, tx index and tx value.

see this example to get an idea of how tx contains
{'blockHash': '0x60265fe6cffcbd2dc5f3872c4eb151e17919296270210985df3ef2249d99171c',
 'blockNumber': '0x63973b',
 'from': '0x5e032243d507c743b061ef021e2ec7fcc6d3ab89',
 'gas': '0xafc8',
 'gasPrice': '0xcce416600',
 'hash': '0x940cdd338b4ec8f9b2b63c01a88683f8658f9a388d79873c6bb913b34e579dd8',
 'input': '0x',
 'nonce': '0x193dd',
 'r': '0xcffe406e06ac7f5049798785d1ead4d9420aa763838592e275b997d6efb411d7',
 's': '0x5db6e46eae1dae407b4e54c49e50ccb17a41a6569cb848aae021f06d4d7fb450',
 'to': '0xf67fa6500b490a05c29a47b40a9e3b72e3044a15',
 'transactionIndex': '0x0',
 'v': '0x26',
 'value': '0x4563918244f40000'}
'''
txlist = [i for sublist in txlist for i in sublist] # a list of all the retrieved transactions

'''
txData: a list of the data needed for our benchmarking system.
It contains tx hash, gas limit, used gas, gas price, receipint address, byte code for contract creation and byte code for function execution (input).
'''
txdata= [["" for x in range(7)] for y in range(len(txlist))] #

blocks = []
usedgas = []
gaslimit=[]
gasprice=[] # in Gwei
to=[] # contract address
input=[] # bytecode for contract's transaction
contract=[] #byte code for contract

for i in range(len(txlist)):
    try:

        if (myapi.getCode(txlist[i]['to']) != ""):
            txdata[i][0]= txlist[i]['hash'] # hash of the transaction
            txdata[i][1]= int(txlist[i]['gas'],16) # gas limit of the transaction
            usedgas = myapi.getTransactionReceipt(txlist[i]['hash']) # get used gas of the transaction
            txdata[i][2]= int(usedgas['gasUsed'],16) # used gas of the transaction
            txdata[i][3] = (int(txlist[i]['gasPrice'],16)/1000000000) # gas price (in Gwei) of the transaction
            txdata[i][4] = txlist[i]['to'] # receipint of the transaction
            txdata[i][6] = txlist[i]['input']#[:32767]# byte code (input) for transaction execution
            #txdata[i][8] = txlist[i]['input'][32767:]# byte code (input) for transaction execution

            if txlist[i]['to'] != "":
                creation_code= get_contractCreation_code(txlist[i]['to']) # byte code for contract creation
                txdata[i][5] = creation_code # byte code for contract creation
            else: txdata[i][5] = "Contract Creation"
        else:
            print("financial transaction!")


    except Exception as exception:
        time.sleep (1)  # Seconds


df=pd.DataFrame(txdata)
df.columns = ['txHash','gas limit', 'used gas', 'gas price','to', 'creation code', 'execution code']
# writer = pd.ExcelWriter('Ret10k01.xlsx', engine='xlsxwriter')
# df.to_excel(writer, sheet_name='Transactions')
# writer.save()
df.to_csv('Ret10k01.csv')





#
#
#
#
#
#
#
#
#
#
#
#
#
# Cinput=[]
#
# ExcelFileName = 'try.xlsx'
# workbook = xlrd.open_workbook(ExcelFileName)
# worksheet = workbook.sheet_by_name("Sheet1") # We need to read the data
#
# num_rows = worksheet.nrows  #Number of Rows
# num_cols = worksheet.ncols  #Number of Columns
#
# result= [[0 for x in range(2)] for y in range(3)]
# for curr_row in range(0,3, 1):
#         row_data = []
#         tt=[] # tem results
#
#         for curr_col in range(0, num_cols, 1):
#             data = worksheet.cell_value(curr_row, curr_col) # Read the data in the current cell
#             row_data.append(data)
#
#         if row_data[4] != "Contract Creation":
#            add= row_data[3]
#            try:
#                tt= myapi.getTransactions(add,0,9999999999,1,1)
#                inp= tt[0]['input']
#                TO = tt[0]['to']
#                if (TO == ''):
#                    Cinput += [inp]
#                    result[curr_row][0]= inp[:32767]
#                    result[curr_row][1]= inp[32767:]
#                    x= result[curr_row][0] + result[curr_row][1]
#                    print(x)
#
#                else:
#                    Cinput += ["error"]
#                    result[curr_row][0]= "error"
#                    result[curr_row][1]= "error"
#
#            except Exception:
#                Cinput += ["error"]
#                result[curr_row][0]= "error"
#                result[curr_row][1]= "error"
#
#            #TO= tt[0]['to']
#         #if (TO == ''):
#          #   Cinput += [inp]
#         #else:
#          #   Cinput += ["error"]
#         else:
#             Cinput += [row_data[4]]
#             y1+=[row_data[4]]
#             y2+=["error"]
#
#
#
# C = pd.DataFrame(result)
#
# writer = pd.ExcelWriter('xx.xlsx', engine='xlsxwriter')
#
# C.to_excel(writer, sheet_name='Contracts')
# #C.to_csv('trry.csv', sep='\t')
# writer.save()
