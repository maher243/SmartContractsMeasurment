import json
import logging
from ethereum import transactions
from ethereum.state import State
from ethereum.config import Env
from ethereum import messages as pb
from ethereum import utils as u
from ethereum.slogging import LogRecorder, configure, get_logger, get_logger_names, get_configuration
from ethereum import block
from ethereum.db import EphemDB
import os
import sys
from collections import Counter
from string import digits
import numpy as np
import scipy as sp
import scipy.stats
import statistics
import csv
import xlrd
import pandas as pd
import codecs
import numpy as np
from timeit import default_timer as timer
from openpyxl import load_workbook
import psutil

sys.setrecursionlimit(10000000)
_env = Env(EphemDB())

ExcelFileName = 'DataSet8.xlsx'
workbook = xlrd.open_workbook(ExcelFileName)
worksheet = workbook.sheet_by_name("Set1") # We need to read the data
num_tx=10


num_runs=10
blockLimit = 8100000
result= [[0 for x in range(9)] for y in range(num_tx)]

# @profile
def profile_vm_test(params, _):
    pre = params['pre']
    exek = params['exec']
    env = params['env']
    index=0

    # setup env
    blkh = block.BlockHeader(prevhash=codecs.decode(env['previousHash'],'hex'), number=int(env['currentNumber']),
                             coinbase=env['currentCoinbase'],
                             difficulty=int(env['currentDifficulty']),
                             gas_limit=int(env['currentGasLimit']),
                             timestamp=int(env['currentTimestamp']))
    block.Block(blkh, db=_env)
    state = State(env=_env, block_number=int(env['currentNumber']),
                  block_coinbase=env['currentCoinbase'],
                  block_difficulty=int(env['currentDifficulty']),
                  gas_limit=int(env['currentGasLimit']),
                  timestamp=int(env['currentTimestamp']))

    # setup state
    for address, h in pre.items():
        state.set_nonce(address, int(h['nonce']))
        state.set_balance(address, int(h['balance']))
        state.set_balance("cd1722f3947def4cf144679da39c4c32bdc35681", int(h['balance']))
        state.set_code(address, codecs.decode(h['code'][2:],'hex'))
        for k, v in h['storage'].items():
            state.set_storage_data(address,
                                   u.big_endian_to_int(codecs.decode(k[2:],'hex')),
                                   u.big_endian_to_int(codecs.decode(v[2:],'hex')))

    for curr_row in range(1,num_tx+1,1):
        state = State(env=_env, block_number=int(env['currentNumber']),
                      block_coinbase=env['currentCoinbase'],
                      block_difficulty=int(env['currentDifficulty']),
                      gas_limit=int(env['currentGasLimit']),
                      timestamp=int(env['currentTimestamp']))

        nonce=0
        conBench(state,exek,curr_row,nonce,index)
        nonce = nonce + 1
        index+=1

    df = pd.DataFrame(result)
    df.columns = ['TX', 'Type','Used gas', 'minTime', 'maxTime', 'avgTime', 'medTime', 'stdevTime', 'CI(95%)']
    writer = pd.ExcelWriter('BenchmarkResults8U.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Set8')
    writer.save()


def conBench(state,exek,curr_row,_nonce,index):
    ################################### Start contracts' benchmarking ###################################

    Ugas=0
    exTime = []
    gasUsed = []
    minTime=0
    maxTime=0
    avgTime=0
    medTime=0
    stdevTime=0
    CITime=0
    type="Execution"

    #### prepare creation & execution bytecodes for benchmarking ####
    if worksheet.cell_value(curr_row, 5) != "":
        creation_bytecode = worksheet.cell_value(curr_row, 4) + worksheet.cell_value(curr_row, 5)
    else:
        creation_bytecode = worksheet.cell_value(curr_row, 4)
    if worksheet.cell_value(curr_row, 7) != "":
        execution_bytecode=  worksheet.cell_value(curr_row, 6) + worksheet.cell_value(curr_row, 7)
    else:
        execution_bytecode=  worksheet.cell_value(curr_row, 6)

    ##### if transaction is to invoke a contract, we first need to deploy the contract #####
    if creation_bytecode != "Contract Creation":
        try:
            tx1 = transactions.Transaction(
                nonce=_nonce,
                gasprice=int(exek['gasPrice']),
                startgas=int(exek['gas']),
                to="",
                value=0,
                data=codecs.decode(creation_bytecode[2:],'hex'),
                r=1, s=2, v=27)
            tx1._sender = exek['origin']
            _nonce = _nonce + 1
            success, address,t,g = pb.apply_transaction(state, tx1)
            if g > blockLimit: success=0; address=""
        except Exception:
            success=0; address=""
            pass

    elif creation_bytecode == "Contract Creation": # if transaction is to create a contract, make address empty and pass for next test
        type="Creation"
        address=""
        success=1

    #################### test transaction execution ########################
    ################ test if execution works or not, before conducting the benchmark #######################
    if success == 1: # if contract was crteated successfully
        try:
            tx2 = transactions.Transaction(
                nonce=_nonce,
                gasprice=int(exek['gasPrice']),
                startgas=int(exek['gas']),
                to=address,
                value=0,
                data=codecs.decode(execution_bytecode[2:],'hex'),
                r=1, s=2, v=27)
            tx2._sender = exek['origin']
            success1, output1, t, g = pb.apply_transaction(state, tx2)
            if g > blockLimit: success1=0
        except Exception:
            success1=0
            pass
        _nonce = _nonce + 1


        #################### transactions' benchmarking ########################
        if success1 ==1: # if contract was created successfully  or if transaction is to create a new contract
            if type=="creation": address=""
            attempts=0
            while attempts <10: # attempt the benchmark up to 10 times if confidence interval is more than 2% of the average value
                exTime=[]
                gasUsed=[]
                for i in range(num_runs):
                        try:
                            txInvoke = transactions.Transaction(
                                nonce=_nonce,
                                gasprice=int(exek['gasPrice']),
                                startgas=int(exek['gas']),
                                to=address,
                                value=0,
                                data=codecs.decode(execution_bytecode[2:],'hex'),
                                r=1, s=2, v=27)
                            txInvoke._sender = exek['origin']
                            success2, output2, time, gas = pb.apply_transaction(state, txInvoke)
                            if gas > blockLimit: gas=0; time=0
                        except Exception:
                            time=0
                            gas=0
                            pass

                        _nonce = _nonce + 1
                        exTime.append(time)
                        gasUsed.append(gas)

                minTime=round(min(exTime),0)
                maxTime=round(max(exTime),0)
                avgTime=round(np.mean(exTime),0)
                medTime=round(statistics.median(exTime),0)
                stdevTime=round(statistics.stdev(exTime),0)
                if min(gasUsed) == max(gasUsed):
                    Ugas = max(gasUsed)
                else:
                    Ugas =0
                CITime=mean_confidence_interval(exTime)

                if Ugas !=0 and (CITime/avgTime*100)>2.0:
                    attempts +=1
                else:
                    break

    result[index][0]= worksheet.cell_value(curr_row, 1)
    result[index][1]= type
    result[index][2]= Ugas
    result[index][3]= minTime
    result[index][4]= maxTime
    result[index][5]= avgTime
    result[index][6]= medTime
    result[index][7]= stdevTime
    result[index][8]= CITime

#read state info from the json file
def recursive_list(d):
    files = []
    dirs = [d]
    i = 0
    while i < len(dirs):
        if os.path.isdir(dirs[i]):
            children = [os.path.join(dirs[i], f) for f in os.listdir(dirs[i])]
            for f in children:
                dirs.append(f)
        elif dirs[i][-5:] == '.json':
                files.append(dirs[i])
        i += 1
    return files

# compute the confidence interval
def mean_confidence_interval(data, confidence=0.95):
    a = 1.0*np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * sp.stats.t._ppf((1+confidence)/2., n-1)
    #return round(m-h), round(m+h)
    return round(h)


def main():
    vm_files = recursive_list(sys.argv[1]) # calldatacop json file

    for i, f in enumerate(vm_files):
        j = json.load(open(f))
        for _, t in j.items():
            profile_vm_test(t, _)

if __name__ == '__main__':
    main()
